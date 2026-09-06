"""WebSocket transports for local perception and landmark ingestion.

The browser never sends tracking images to the HTTP backend. A local
RTMLib worker receives a short-lived camera frame over its private WebSocket,
returns canonical landmarks, and the browser forwards only those landmarks to
the backend WebSocket. This keeps the backend boundary landmark-only.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
from collections import defaultdict, deque
from typing import Any

from .models import PayloadValidationError, SignSequencePayload
from .classifier_features import ClassifierFeatureEngine
from .processing_contracts import build_gloss_lattice
from .segmentation import PhraseSegmenter
from .service import SignBridgeBackend

MAX_CAMERA_BYTES = 2 * 1024 * 1024
MAX_MESSAGE_BYTES = 3 * 1024 * 1024


def _websocket_serve():
    try:
        from websockets.asyncio.server import serve
    except ImportError:  # websockets 13/14 compatibility
        from websockets.server import serve
    return serve


def _required_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{field} must be an object")
    return value


def _finite(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise PayloadValidationError(f"{field} must be a number")
    result = float(value)
    if result != result or result in (float("inf"), float("-inf")):
        raise PayloadValidationError(f"{field} must be finite")
    return result


def validate_landmark_frame(message: Any) -> dict[str, Any]:
    """Validate the small canonical frame sent across the backend seam."""
    value = _required_object(message, "message")
    if value.get("type") != "landmark_frame":
        raise PayloadValidationError("message.type must be landmark_frame")
    stream_id = value.get("stream_id")
    if not isinstance(stream_id, str) or not stream_id.strip():
        raise PayloadValidationError("stream_id must be a non-empty string")
    frame = _required_object(value.get("frame"), "frame")
    hands = frame.get("hands", [])
    normalized = frame.get("normalized_coordinates", [])
    for field, collection in (("hands", hands), ("normalized_coordinates", normalized)):
        if not isinstance(collection, list) or len(collection) > 2:
            raise PayloadValidationError(f"frame.{field} must contain at most two hands")
        for hand_index, hand in enumerate(collection):
            hand = _required_object(hand, f"frame.{field}[{hand_index}]")
            landmarks = hand.get("landmarks", [])
            if not isinstance(landmarks, list) or len(landmarks) != 21:
                raise PayloadValidationError(
                    f"frame.{field}[{hand_index}].landmarks must contain 21 points"
                )
            for point_index, point in enumerate(landmarks):
                point = _required_object(point, f"frame.{field}[{hand_index}].landmarks[{point_index}]")
                for axis in ("x", "y", "z"):
                    _finite(point.get(axis), f"landmark.{axis}")
    _finite(
        frame.get("tracking_confidence", frame.get("processing_confidence", 0)),
        "frame.tracking_confidence",
    )
    return {"stream_id": stream_id, "frame": frame}


class LandmarkStream:
    def __init__(self, service: SignBridgeBackend) -> None:
        self.service = service
        self.frames: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=180)
        )
        self.segmenter = PhraseSegmenter()
        self.classifier_features = ClassifierFeatureEngine()
        self.emitted_segment_ends: dict[str, int] = defaultdict(lambda: -1)
        self.lattice_sequences: dict[str, int] = defaultdict(lambda: 0)

    async def handler(self, websocket: Any) -> None:
        async for raw in websocket:
            try:
                if not isinstance(raw, str) or len(raw.encode()) > MAX_MESSAGE_BYTES:
                    raise PayloadValidationError("WebSocket message is too large")
                decoded = json.loads(raw)
                if isinstance(decoded, dict) and decoded.get("type") == "sequence":
                    payload = SignSequencePayload.from_dict(decoded.get("payload"))
                    result = await asyncio.to_thread(self.service.analyze, payload)
                    await websocket.send(json.dumps({
                        "type": "sequence_result",
                        "request_id": decoded.get("request_id"),
                        "result": result,
                    }))
                    continue
                message = validate_landmark_frame(decoded)
                stream_id = message["stream_id"]
                self.frames[stream_id].append(message["frame"])
                buffered_frames = list(self.frames[stream_id])
                completed_segments = [
                    segment
                    for segment in self.segmenter.segment(buffered_frames)
                    if segment.end_index < len(buffered_frames) - 1
                    and segment.end_index > self.emitted_segment_ends[stream_id]
                ]
                for segment in completed_segments:
                    features = self.classifier_features.extract(
                        segment.frames,
                        phrase_id=segment.phrase_id,
                        prior_frames=buffered_frames[: segment.start_index],
                    )
                    feature_window = self.classifier_features.build_feature_window(segment).to_dict()
                    classifier_output = self.service.analyzer._classify_phrase(features)
                    classifier_output["schema_version"] = "1.0"
                    classifier_output["feature_window_id"] = feature_window["window_id"]
                    self.emitted_segment_ends[stream_id] = segment.end_index
                    await websocket.send(json.dumps({
                        "type": "phrase_segment",
                        "stream_id": stream_id,
                        "segment": segment.to_dict(),
                        "classifier_features": features,
                        "feature_window": feature_window,
                        "classifier_output": classifier_output,
                    }))
                    self.lattice_sequences[stream_id] += 1
                    lattice = build_gloss_lattice(
                        session_id=stream_id,
                        utterance_id=segment.phrase_id,
                        language="unknown",
                        started_at=(segment.frames[0].get("timestamp") if segment.frames else None),
                        ended_at=(segment.frames[-1].get("timestamp") if segment.frames else None),
                        phrases=[{
                            "phrase_id": segment.phrase_id,
                            "feature_window": feature_window,
                            "classifier_output": classifier_output,
                        }],
                        producer={
                            "segmenter_arm": segment.segmenter_arm,
                            "classifier_id": "signbridge_temporal_classifier",
                            "classifier_version": self.service.analyzer.model_version,
                            "calibration_version": "none",
                            "vocabulary_version": "unknown",
                        },
                        lattice_seq=self.lattice_sequences[stream_id],
                    )
                    await websocket.send(json.dumps({
                        "type": "gloss_lattice",
                        "stream_id": stream_id,
                        "lattice": lattice,
                    }))
                await websocket.send(json.dumps({
                    "type": "landmark_ack",
                    "stream_id": stream_id,
                    "sequence": message["frame"].get("sequence"),
                    "buffered_frames": len(self.frames[stream_id]),
                }))
            except (json.JSONDecodeError, PayloadValidationError) as error:
                await websocket.send(json.dumps({"type": "error", "error": str(error)}))


class PerceptionStream:
    def __init__(self, service: SignBridgeBackend) -> None:
        self.service = service

    async def handler(self, websocket: Any) -> None:
        async for raw in websocket:
            try:
                if not isinstance(raw, str) or len(raw.encode()) > MAX_MESSAGE_BYTES:
                    raise PayloadValidationError("WebSocket message is too large")
                message = _required_object(json.loads(raw), "message")
                if message.get("type") != "camera_frame":
                    raise PayloadValidationError("message.type must be camera_frame")
                encoded = message.get("image_base64")
                if not isinstance(encoded, str) or not encoded:
                    raise PayloadValidationError("image_base64 is required")
                if encoded.startswith("data:") and "," in encoded:
                    encoded = encoded.split(",", 1)[1]
                image_bytes = base64.b64decode(encoded, validate=True)
                if not image_bytes or len(image_bytes) > MAX_CAMERA_BYTES:
                    raise PayloadValidationError("camera frame size is invalid")
                result = await asyncio.to_thread(self.service.track_frame, image_bytes)
                await websocket.send(json.dumps({
                    "type": "landmark_frame",
                    "timestamp_ms": message.get("timestamp_ms"),
                    **result,
                }))
            except (json.JSONDecodeError, binascii.Error, PayloadValidationError) as error:
                await websocket.send(json.dumps({"type": "error", "error": str(error)}))
            except RuntimeError as error:
                await websocket.send(json.dumps({"type": "error", "error": str(error)}))


def make_servers(service: SignBridgeBackend, host: str, tracking_port: int, perception_port: int):
    """Return an asyncio coroutine that starts both local WebSocket servers."""
    serve = _websocket_serve()
    landmark_stream = LandmarkStream(service)
    perception_stream = PerceptionStream(service)

    async def start():
        tracking_server = await serve(landmark_stream.handler, host, tracking_port)
        perception_server = await serve(perception_stream.handler, host, perception_port)
        return tracking_server, perception_server

    return start
