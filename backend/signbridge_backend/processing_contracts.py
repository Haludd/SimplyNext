"""Explicit contracts for the perception-to-classifier pipeline.

The pipeline intentionally has only three hand-off shapes:

* ``LandmarkFrame``: one fully normalised frame entering segmentation.
* ``FeatureWindow`` + ``BoundaryEvent``: one segmented window entering the
  classifier and calibration stages.
* ``GlossLattice``: compact top-k evidence leaving calibration for the
  backend WebSocket. It never contains raw landmarks.

The raw frontend keys are retained for compatibility, but every typed frame
also exposes grouped landmark data, per-point confidence, handedness and
running confidence averages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


PROCESSING_SCHEMA_VERSION = "1.0"

_SHOULDER_KEYS = ("left_shoulder", "right_shoulder")
_ARM_KEYS = ("left_elbow", "right_elbow", "left_wrist", "right_wrist")
_POSE_KEYS = ("left_hip", "right_hip", "nose", "neck")


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if result == result and abs(result) != float("inf") else default


def _confidence(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


def _point(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if not all(axis in value for axis in ("x", "y", "z")):
        return None
    point = {
        "x": _number(value.get("x")),
        "y": _number(value.get("y")),
        "z": _number(value.get("z")),
        "confidence": _confidence(
            value.get("confidence", value.get("visibility", 1.0))
        ),
    }
    for key in ("world_x", "world_y", "world_z"):
        if key in value:
            point[key] = _number(value.get(key))
    return point


def _timestamp_ms(value: Any, fallback: int = 0) -> int:
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(
                0,
                int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000),
            )
        except ValueError:
            pass
    return max(0, fallback)


def _as_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _normalization_metadata(value: dict[str, Any], normalized: list[dict[str, Any]]) -> dict[str, Any]:
    supplied = value.get("normalization")
    if isinstance(supplied, dict):
        return dict(supplied)
    return {
        "coordinate_space": (
            "shoulder_centered_normalized_3d" if normalized else "image_normalized"
        ),
        "source": "stage_3_body_normalization" if normalized else "legacy_frame",
    }


def _group_landmarks(
    value: dict[str, Any],
    hands: list[dict[str, Any]],
    normalized: list[dict[str, Any]],
) -> dict[str, Any]:
    """Organise the stream into stable, human-readable body sections."""
    shoulders = {
        key: point
        for key in _SHOULDER_KEYS
        if (point := _point(value.get(key))) is not None
    }
    arms = {
        key: point
        for key in _ARM_KEYS
        if (point := _point(value.get(key))) is not None
    }
    pose = {
        key: point
        for key in _POSE_KEYS
        if (point := _point(value.get(key))) is not None
    }
    face = value.get("face_expression", value.get("face", {}))
    facial_expression = dict(face) if isinstance(face, dict) else {}
    return {
        "shoulders": shoulders,
        "arms": arms,
        "pose": pose,
        "hands": normalized or hands,
        "facial_expression": facial_expression,
    }


def _group_presence(groups: dict[str, Any]) -> dict[str, bool]:
    return {
        "shoulders": bool(groups.get("shoulders")),
        "arms": bool(groups.get("arms")),
        "pose": bool(groups.get("pose")),
        "hands": bool(groups.get("hands")),
        "facial_expression": bool(groups.get("facial_expression")),
    }


def _frame_hand_averages(value: dict[str, Any]) -> dict[str, float]:
    result = {"left": 0.0, "right": 0.0, "unknown": 0.0}
    for hand in _as_list(value.get("hands")):
        handedness = str(hand.get("handedness", "unknown")).lower()
        if handedness not in result:
            handedness = "unknown"
        result[handedness] = _confidence(hand.get("confidence"))
    return result


@dataclass(frozen=True)
class LandmarkFrame:
    """Stage-③ output consumed by the stage-④ segmenter."""

    frame_index: int
    timestamp: str | None
    hands: list[dict[str, Any]]
    tracking_confidence: float
    normalized_coordinates: list[dict[str, Any]]
    raw: dict[str, Any]
    schema_version: str = PROCESSING_SCHEMA_VERSION
    landmark_groups: dict[str, Any] = field(default_factory=dict)
    group_presence: dict[str, bool] = field(default_factory=dict)
    running_averages: dict[str, Any] = field(default_factory=dict)
    normalization: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        value: dict[str, Any],
        frame_index: int,
        *,
        running_averages: dict[str, Any] | None = None,
    ) -> "LandmarkFrame":
        hands = _as_list(value.get("hands"))
        normalized = _as_list(
            value.get("normalized_coordinates", value.get("body_normalized_coordinates", []))
        )
        groups = _group_landmarks(value, hands, normalized)
        averages = running_averages or {
            "tracking_confidence": _confidence(
                value.get("tracking_confidence", value.get("processing_confidence"))
            ),
            "hands": _frame_hand_averages(value),
        }
        return cls(
            frame_index=frame_index,
            timestamp=value.get("timestamp"),
            hands=hands,
            tracking_confidence=_confidence(
                value.get("tracking_confidence", value.get("processing_confidence"))
            ),
            normalized_coordinates=normalized,
            raw=value,
            schema_version=str(value.get("schema_version", PROCESSING_SCHEMA_VERSION)),
            landmark_groups=groups,
            group_presence=_group_presence(groups),
            running_averages=averages,
            normalization=_normalization_metadata(value, normalized),
        )

    @classmethod
    def from_sequence(
        cls,
        frames: Iterable[dict[str, Any] | "LandmarkFrame"],
    ) -> list["LandmarkFrame"]:
        """Attach deterministic running confidence averages to each frame."""
        totals = {"tracking_confidence": 0.0, "left": 0.0, "right": 0.0, "unknown": 0.0}
        counts = {"tracking_confidence": 0, "left": 0, "right": 0, "unknown": 0}
        result: list[LandmarkFrame] = []
        for index, item in enumerate(frames):
            if isinstance(item, LandmarkFrame):
                value = item.to_dict()
                frame_index = item.frame_index
            elif isinstance(item, dict):
                value = item
                frame_index = index
            else:
                continue
            tracking = _confidence(
                value.get("tracking_confidence", value.get("processing_confidence"))
            )
            totals["tracking_confidence"] += tracking
            counts["tracking_confidence"] += 1
            hand_values = _frame_hand_averages(value)
            for side, confidence in hand_values.items():
                if confidence <= 0:
                    continue
                totals[side] += confidence
                counts[side] += 1
            averages = {
                "tracking_confidence": round(
                    totals["tracking_confidence"] / max(counts["tracking_confidence"], 1), 6
                ),
                "hands": {
                    side: round(totals[side] / max(counts[side], 1), 6)
                    for side in ("left", "right", "unknown")
                },
            }
            result.append(cls.from_dict(value, frame_index, running_averages=averages))
        return result

    def to_dict(self) -> dict[str, Any]:
        value = dict(self.raw)
        value.update({
            "schema_version": self.schema_version,
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "tracking_confidence": self.tracking_confidence,
            "normalized_coordinates": self.normalized_coordinates,
            "landmark_groups": self.landmark_groups,
            "group_presence": self.group_presence,
            "running_averages": self.running_averages,
            "normalization": self.normalization,
        })
        return value


@dataclass(frozen=True)
class BoundaryEvent:
    event_type: str
    frame_index: int
    reason: str
    segmenter_arm: str = "geometry_hysteresis"
    confidence: float = 1.0
    schema_version: str = PROCESSING_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "frame_index": self.frame_index,
            "reason": self.reason,
            "segmenter_arm": self.segmenter_arm,
            "confidence": round(_confidence(self.confidence), 6),
        }


@dataclass
class FeatureWindow:
    """Stage-④ output handed from segmentation to classification."""

    window_id: str
    frame_range: dict[str, int]
    normalized_coordinates: list[dict[str, Any]]
    velocity: list[dict[str, Any]]
    acceleration: list[dict[str, Any]]
    segmenter_arm: str
    confidence: dict[str, Any]
    boundary_events: list[BoundaryEvent] = field(default_factory=list)
    schema_version: str = PROCESSING_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "window_id": self.window_id,
            "frame_range": self.frame_range,
            "frame_index_range": self.frame_range,
            "normalized_coordinates": self.normalized_coordinates,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "segmenter_arm": self.segmenter_arm,
            "confidence": self.confidence,
            "boundary_events": [event.to_dict() for event in self.boundary_events],
        }


def _candidate(value: dict[str, Any], rank: int) -> dict[str, Any]:
    gloss_id = str(value.get("gloss_id", value.get("gloss", "UNKNOWN")))
    score = _confidence(value.get("score", value.get("confidence", 0.0)))
    confidence = _confidence(value.get("confidence", score))
    return {
        "rank": rank,
        "gloss_id": gloss_id,
        "gloss": gloss_id,
        "score": round(score, 6),
        "confidence": round(confidence, 6),
    }


@dataclass(frozen=True)
class GlossLatticeSlot:
    """One classifier/calibration decision slot with no landmark payload."""

    slot_index: int
    slot_id: str
    frame_range: dict[str, int]
    candidates: list[dict[str, Any]]
    class_scores: dict[str, float]
    confidence: float
    provenance: str
    refused: bool
    calibrated: bool
    segmenter_arm: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_index": self.slot_index,
            "slot_id": self.slot_id,
            "frame_range": self.frame_range,
            "candidates": self.candidates,
            "class_scores": self.class_scores,
            "confidence": round(_confidence(self.confidence), 6),
            "provenance": self.provenance,
            "refused": self.refused,
            "calibrated": self.calibrated,
            "segmenter_arm": self.segmenter_arm,
        }


@dataclass(frozen=True)
class GlossLattice:
    """Compact stage-⑥ message sent over the backend WebSocket."""

    session_id: str
    utterance_id: str
    language: str
    started_at_ms: int
    ended_at_ms: int
    producer: dict[str, Any]
    slots: list[GlossLatticeSlot]
    lattice_seq: int = 1
    timebase: str = "unix_epoch_ms"
    schema_version: str = PROCESSING_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "gloss_lattice",
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "lattice_seq": self.lattice_seq,
            "utterance_id": self.utterance_id,
            "language": self.language,
            "timebase": self.timebase,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "producer": self.producer,
            "slots": [slot.to_dict() for slot in self.slots],
        }


def build_gloss_lattice(
    *,
    session_id: str,
    utterance_id: str,
    language: str,
    started_at: Any,
    ended_at: Any,
    phrases: Iterable[dict[str, Any]],
    producer: dict[str, Any],
    lattice_seq: int = 1,
) -> dict[str, Any]:
    """Build the exact compact object used at the calibration/WebSocket seam."""
    slots: list[GlossLatticeSlot] = []
    for index, phrase in enumerate(phrases):
        feature_window = phrase.get("feature_window") or {}
        classifier = phrase.get("classifier_output") or {}
        raw_candidates = classifier.get("top_k_glosses", phrase.get("top_k_glosses", []))
        candidates = [
            _candidate(item, rank)
            for rank, item in enumerate(raw_candidates, start=1)
            if isinstance(item, dict)
        ]
        top_confidence = _confidence(
            classifier.get("confidence", candidates[0]["confidence"] if candidates else 0.0)
        )
        frame_range = feature_window.get("frame_range", {"start": 0, "end": 0})
        slots.append(GlossLatticeSlot(
            slot_index=index,
            slot_id=str(phrase.get("phrase_id", f"phrase_{index + 1:03d}")),
            frame_range={
                "start": int(frame_range.get("start", 0)),
                "end": int(frame_range.get("end", frame_range.get("start", 0))),
            },
            candidates=candidates,
            class_scores={
                str(key): round(_confidence(value), 6)
                for key, value in (classifier.get("class_scores") or {}).items()
            },
            confidence=top_confidence,
            provenance=str(classifier.get("provenance", "unresolved")),
            refused=bool(classifier.get("refused", True)),
            calibrated=bool(classifier.get("calibrated", False)),
            segmenter_arm=str(feature_window.get("segmenter_arm", "unknown")),
        ))
    return GlossLattice(
        session_id=str(session_id),
        utterance_id=str(utterance_id),
        language=str(language),
        started_at_ms=_timestamp_ms(started_at),
        ended_at_ms=_timestamp_ms(ended_at),
        producer=dict(producer),
        slots=slots,
        lattice_seq=max(1, int(lattice_seq)),
    ).to_dict()
