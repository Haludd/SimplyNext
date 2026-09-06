"""Feature processing for classifier handshapes, trajectories, space, and NMMs.

The output is intentionally a feature/token representation, not a claim that
the engine has translated ASL. Handshape labels are conservative geometric
proposals that a trained sign-language classifier can consume or override.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import math
from statistics import median
from typing import Any, Iterable

from .processing_contracts import FeatureWindow
from .segmentation import hand_centers


@dataclass(frozen=True)
class FeatureAssemblyConfig:
    """T4.1 feature budget, kept configurable instead of hard-coded."""

    hand_landmark_indices: tuple[int, ...] = tuple(range(21))
    pose_keys: tuple[str, ...] = (
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
    )
    face_blendshape_keys: tuple[str, ...] = (
        "browInnerUp",
        "browOuterUpLeft",
        "browOuterUpRight",
        "browDownLeft",
        "browDownRight",
        "mouthSmileLeft",
        "mouthSmileRight",
        "mouthFrownLeft",
        "mouthFrownRight",
        "jawOpen",
        "mouthPucker",
    )
    include_confidence: bool = True
    include_presence: bool = True

    @property
    def hand_slot_dimension(self) -> int:
        per_point = 4 if self.include_confidence else 3
        return len(self.hand_landmark_indices) * per_point + (1 if self.include_presence else 0)

    @property
    def feature_dimension(self) -> int:
        return 2 * self.hand_slot_dimension + len(self.pose_keys) * 4 + len(self.face_blendshape_keys)

    def schema(self) -> dict[str, Any]:
        return {
            "hand_landmark_indices": list(self.hand_landmark_indices),
            "pose_keys": list(self.pose_keys),
            "face_blendshape_keys": list(self.face_blendshape_keys),
            "include_confidence": self.include_confidence,
            "include_presence": self.include_presence,
            "feature_dimension": self.feature_dimension,
        }


def _number(value: Any, fallback: float = 0.0) -> float:
    try:
        value = float(value)
        return value if math.isfinite(value) else fallback
    except (TypeError, ValueError):
        return fallback


def _point(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, dict):
        return None
    return (_number(value.get("x")), _number(value.get("y")), _number(value.get("z")))


def _timestamp(frame: dict[str, Any], index: int) -> float:
    value = frame.get("timestamp")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return _number(frame.get("timestamp_ms"), index * 33.0) / (1000.0 if "timestamp_ms" in frame else 1.0)


def _distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.sqrt(sum((first[index] - second[index]) ** 2 for index in range(3)))


class ClassifierFeatureEngine:
    """Extract structured classifier features from one temporal phrase."""

    def __init__(self, config: FeatureAssemblyConfig | None = None) -> None:
        self.config = config or FeatureAssemblyConfig()

    @property
    def feature_dimension(self) -> int:
        return self.config.feature_dimension

    def extract(
        self,
        frames: Iterable[dict[str, Any]],
        *,
        phrase_id: str = "phrase_001",
        prior_frames: Iterable[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        values = [frame for frame in frames if isinstance(frame, dict)]
        prior = [frame for frame in prior_frames if isinstance(frame, dict)]
        hand_observations = self._hand_observations(values)
        shape = self._majority_handshape(hand_observations)
        anchor = self._anchor(prior, values)
        trajectory = self._trajectory(values)
        spatial = self._spatial_coordinates(values)
        nmm = self._non_manual_markers(values)
        feature_sequence = self.assemble_sequence(values)
        return {
            "phrase_id": phrase_id,
            "anchor_noun": anchor["value"],
            "anchor_source": anchor["source"],
            "anchor_confidence": anchor["confidence"],
            "classifier_handshape": shape["label"],
            "handshape_confidence": shape["confidence"],
            "handshape_observations": shape["observations"],
            "trajectory": trajectory["label"],
            "trajectory_features": trajectory,
            "spatial_coordinates": spatial["coordinates"],
            "spatial_mapping": spatial,
            "non_manual_markers": nmm,
            "feature_sequence": feature_sequence,
            "feature_schema": self.config.schema(),
            "feature_dimension": self.feature_dimension,
            "feature_status": "geometric_proposal",
        }

    def assemble_sequence(self, frames: Iterable[dict[str, Any]]) -> list[list[float]]:
        """Assemble one fixed-width vector per frame for a temporal model."""
        return [self._assemble_frame(frame) for frame in frames if isinstance(frame, dict)]

    def _assemble_frame(self, frame: dict[str, Any]) -> list[float]:
        normalized_hands = self._normalized_hands(frame)
        by_side = {
            str(hand.get("handedness", "unknown")).lower(): hand
            for hand in normalized_hands
        }
        vector: list[float] = []
        for side in ("left", "right"):
            hand = by_side.get(side)
            points = hand.get("landmarks", []) if hand else []
            valid_points = {
                index: point
                for index, point in enumerate(points)
                if isinstance(point, dict)
            }
            for landmark_index in self.config.hand_landmark_indices:
                point = valid_points.get(landmark_index)
                vector.extend([
                    _number(point.get("x")) if point else 0.0,
                    _number(point.get("y")) if point else 0.0,
                    _number(point.get("z")) if point else 0.0,
                ])
                if self.config.include_confidence:
                    vector.append(_number(point.get("confidence")) if point else 0.0)
            if self.config.include_presence:
                vector.append(1.0 if hand else 0.0)

        for key in self.config.pose_keys:
            point = _point(frame.get(key))
            visibility = _number((frame.get(key) or {}).get("visibility"), 0.0)
            vector.extend([
                point[0] if point else 0.0,
                point[1] if point else 0.0,
                point[2] if point else 0.0,
                visibility,
            ])

        face = frame.get("face_expression") or frame.get("face") or {}
        blendshapes = face.get("blendshapes", {}) if isinstance(face, dict) else {}
        if not isinstance(blendshapes, dict):
            blendshapes = {}
        vector.extend(_number(blendshapes.get(key)) for key in self.config.face_blendshape_keys)
        return vector

    def build_feature_window(self, segment: Any) -> FeatureWindow:
        """Build the PLN/T2.1 feature contract from one phrase segment."""
        frames = [frame for frame in segment.frames if isinstance(frame, dict)]
        normalized: list[dict[str, Any]] = []
        centers: list[tuple[float, float, float] | None] = []
        point_confidences: list[float] = []
        frame_confidences: list[float] = []

        for local_index, frame in enumerate(frames):
            frame_index = segment.start_index + local_index
            hands = self._normalized_hands(frame)
            normalized.append({"frame_index": frame_index, "hands": hands})
            frame_confidences.append(max(0.0, min(1.0, _number(frame.get("tracking_confidence")))))
            for hand in hands:
                for point in hand.get("landmarks", []):
                    point_confidences.append(_number(point.get("confidence"), 0.0))
            points = [
                _point(point)
                for hand in hands
                for point in hand.get("landmarks", [])[:1]
            ]
            valid = [point for point in points if point is not None]
            centers.append(
                tuple(sum(point[axis] for point in valid) / len(valid) for axis in range(3))
                if valid
                else None
            )

        velocity: list[dict[str, Any]] = []
        acceleration: list[dict[str, Any]] = []
        previous_speed = 0.0
        for index, current in enumerate(centers):
            previous = centers[index - 1] if index else None
            elapsed = max(
                _timestamp(frames[index], index) - _timestamp(frames[index - 1], index - 1),
                1 / 120,
            ) if index else 1 / 30
            if current is None or previous is None:
                vectors: list[dict[str, float]] = []
                speed = _number((frames[index].get("hand_motion") or {}).get("average_speed"))
            else:
                delta = tuple(current[axis] - previous[axis] for axis in range(3))
                speed = _distance(current, previous) / elapsed
                vectors = [{
                    "dx": round(delta[0], 6),
                    "dy": round(delta[1], 6),
                    "dz": round(delta[2], 6),
                    "speed": round(speed, 6),
                }]
            velocity.append({
                "frame_index": segment.start_index + index,
                "magnitude": round(speed, 6),
                "vectors": vectors,
            })
            acceleration.append({
                "frame_index": segment.start_index + index,
                "magnitude": round(abs(speed - previous_speed) / elapsed, 6),
            })
            previous_speed = speed

        confidence_values = [value for value in frame_confidences if value > 0]
        point_values = [value for value in point_confidences if value > 0]
        confidence = {
            "frame_mean": round(sum(confidence_values) / len(confidence_values), 6)
            if confidence_values else 0.0,
            "frame_min": round(min(confidence_values), 6) if confidence_values else 0.0,
            "point_mean": round(sum(point_values) / len(point_values), 6)
            if point_values else 0.0,
            "frame_count": len(frames),
        }
        return FeatureWindow(
            window_id=segment.phrase_id,
            frame_range={"start": segment.start_index, "end": segment.end_index},
            normalized_coordinates=normalized,
            velocity=velocity,
            acceleration=acceleration,
            segmenter_arm=getattr(segment, "segmenter_arm", "geometry_hysteresis"),
            confidence=confidence,
            boundary_events=list(segment.boundary_events or []),
        )

    def _normalized_hands(self, frame: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = frame.get("normalized_coordinates")
        if isinstance(supplied, list) and supplied:
            return [hand for hand in supplied if isinstance(hand, dict)]
        hands = frame.get("hands", [])
        if not isinstance(hands, list):
            return []
        left = _point(frame.get("left_shoulder"))
        right = _point(frame.get("right_shoulder"))
        origin = (
            tuple((left[axis] + right[axis]) / 2 for axis in range(3))
            if left and right else (0.0, 0.0, 0.0)
        )
        scale = _distance(left, right) if left and right else 1.0
        scale = max(scale, 0.1)
        result: list[dict[str, Any]] = []
        for hand in hands:
            if not isinstance(hand, dict):
                continue
            hand_confidence = max(0.0, min(1.0, _number(hand.get("confidence"))))
            landmarks = hand.get("landmarks", [])
            points = []
            if isinstance(landmarks, list):
                for landmark in landmarks:
                    point = _point(landmark)
                    if point is None:
                        continue
                    visibility = _number(landmark.get("visibility"), 1.0) if isinstance(landmark, dict) else 1.0
                    points.append({
                        "x": round((point[0] - origin[0]) / scale, 6),
                        "y": round((point[1] - origin[1]) / scale, 6),
                        "z": round((point[2] - origin[2]) / scale, 6),
                        "confidence": round(hand_confidence * max(0.0, min(1.0, visibility)), 6),
                    })
            result.append({
                "handedness": hand.get("handedness", "unknown"),
                "landmarks": points,
                "confidence": hand_confidence,
            })
        return result

    def _hand_observations(self, frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
        observations: list[dict[str, Any]] = []
        for frame_index, frame in enumerate(frames):
            hands = frame.get("hands", [])
            if not isinstance(hands, list):
                continue
            for hand in hands:
                if not isinstance(hand, dict):
                    continue
                landmarks = hand.get("landmarks", [])
                if len(landmarks) != 21:
                    continue
                label, confidence, metrics = self._handshape(landmarks)
                observations.append({
                    "frame_index": frame_index,
                    "handedness": hand.get("handedness", "unknown"),
                    "label": label,
                    "confidence": confidence,
                    "metrics": metrics,
                })
        return observations

    def _majority_handshape(self, observations: list[dict[str, Any]]) -> dict[str, Any]:
        if not observations:
            return {"label": "UNKNOWN_HANDSHAPE", "confidence": 0.0, "observations": 0}
        labels = [item["label"] for item in observations]
        label, count = Counter(labels).most_common(1)[0]
        confidence = sum(
            item["confidence"] for item in observations if item["label"] == label
        ) / max(count, 1)
        return {
            "label": label,
            "confidence": round(confidence * (count / len(observations)), 6),
            "observations": len(observations),
        }

    def _handshape(self, landmarks: list[Any]) -> tuple[str, float, dict[str, Any]]:
        points = [_point(value) for value in landmarks]
        if any(point is None for point in points):
            return "UNKNOWN_HANDSHAPE", 0.0, {}
        valid = [point for point in points if point is not None]
        wrist = valid[0]
        tips = (4, 8, 12, 16, 20)
        mcps = (2, 5, 9, 13, 17)
        ratios = [
            _distance(valid[tip], wrist) / max(_distance(valid[mcp], wrist), 1e-5)
            for tip, mcp in zip(tips, mcps)
        ]
        extended = [ratio >= 1.18 for ratio in ratios]
        thumb_index_gap = _distance(valid[4], valid[8])
        palm_span = max(_distance(valid[5], valid[17]), 1e-5)
        normalized_gap = thumb_index_gap / palm_span
        extended_count = sum(extended)
        if extended[1] and not any(extended[index] for index in (0, 2, 3, 4)):
            confidence = min(0.99, 0.62 + (ratios[1] - 1.18) * 0.3)
            return "1_HANDSHAPE", confidence, {"extension_ratios": ratios}
        if extended[1] and extended[2] and extended[3] and not extended[4]:
            confidence = min(0.99, 0.62 + (extended_count / 5) * 0.25)
            return "3_HANDSHAPE", confidence, {"extension_ratios": ratios}
        # A C shape keeps the thumb/index opening broad while the fingers
        # remain curved; the exact ratio varies with camera distance, so use
        # a deliberately broad geometric proposal band.
        if extended_count >= 3 and 0.35 <= normalized_gap <= 2.6 and max(ratios) < 3.0:
            return "C_HANDSHAPE", 0.58, {
                "extension_ratios": ratios,
                "thumb_index_gap": normalized_gap,
            }
        if extended_count == 5:
            return "OPEN_5_HANDSHAPE", 0.72, {"extension_ratios": ratios}
        if extended_count == 0:
            return "FIST_HANDSHAPE", 0.72, {"extension_ratios": ratios}
        return "UNKNOWN_HANDSHAPE", 0.3, {"extension_ratios": ratios}

    def _trajectory(self, frames: list[dict[str, Any]]) -> dict[str, Any]:
        points: list[tuple[float, float, float]] = []
        times: list[float] = []
        for index, frame in enumerate(frames):
            centers = hand_centers(frame)
            if centers:
                points.append(tuple(sum(point[axis] for point in centers) / len(centers) for axis in range(3)))
                times.append(_timestamp(frame, index))
        if len(points) < 2:
            return {"label": "STATIONARY", "path_length": 0.0, "displacement": 0.0, "vectors": []}
        vectors = []
        path_length = 0.0
        for index in range(1, len(points)):
            delta = tuple(points[index][axis] - points[index - 1][axis] for axis in range(3))
            elapsed = max(times[index] - times[index - 1], 1 / 120)
            path_length += _distance(points[index], points[index - 1])
            vectors.append({
                "dx": round(delta[0], 6),
                "dy": round(delta[1], 6),
                "dz": round(delta[2], 6),
                "speed": round(_distance(points[index], points[index - 1]) / elapsed, 6),
            })
        displacement = _distance(points[0], points[-1])
        dx = points[-1][0] - points[0][0]
        dy = points[-1][1] - points[0][1]
        dz = points[-1][2] - points[0][2]
        x_sign_changes = self._sign_changes([vector["dx"] for vector in vectors])
        y_sign_changes = self._sign_changes([vector["dy"] for vector in vectors])
        zigzag = (x_sign_changes + y_sign_changes) >= 2 and path_length > max(displacement * 1.35, 0.06)
        if zigzag and dz < -0.02:
            label = "ZIGZAG_FORWARD"
        elif zigzag:
            label = "ZIGZAG"
        elif displacement < 0.035:
            label = "STATIONARY"
        elif abs(dx) >= abs(dy) and abs(dx) >= abs(dz):
            label = "RIGHT" if dx > 0 else "LEFT"
        elif abs(dy) >= abs(dz):
            label = "DOWN" if dy > 0 else "UP"
        else:
            label = "FORWARD" if dz < 0 else "BACKWARD"
        return {
            "label": label,
            "path_length": round(path_length, 6),
            "displacement": round(displacement, 6),
            "net_vector": {"dx": round(dx, 6), "dy": round(dy, 6), "dz": round(dz, 6)},
            "vectors": vectors[-60:],
        }

    @staticmethod
    def _sign_changes(values: list[float]) -> int:
        signs = [1 if value > 0.012 else -1 if value < -0.012 else 0 for value in values]
        nonzero = [value for value in signs if value]
        return sum(nonzero[index] != nonzero[index - 1] for index in range(1, len(nonzero)))

    def _spatial_coordinates(self, frames: list[dict[str, Any]]) -> dict[str, Any]:
        points = [center for frame in frames for center in hand_centers(frame)]
        if not points:
            coordinates = {"x": 0.0, "y": 0.0, "z": 0.0}
            return {"coordinates": coordinates, "coordinate_space": "image_normalized", "entity_placement": None}
        image = {axis: round(median(point[index] for point in points), 6) for index, axis in enumerate(("x", "y", "z"))}
        shoulder_points = []
        for frame in frames:
            left = _point(frame.get("left_shoulder"))
            right = _point(frame.get("right_shoulder"))
            if left and right:
                shoulder_points.append((left, right))
        if shoulder_points:
            left, right = shoulder_points[-1]
            origin = tuple((left[index] + right[index]) / 2 for index in range(3))
            scale = max(_distance(left, right), 0.1)
            relative = {
                "x": round((image["x"] - origin[0]) / scale, 6),
                "y": round((image["y"] - origin[1]) / scale, 6),
                "z": round((image["z"] - origin[2]) / scale, 6),
            }
            return {
                "coordinates": relative,
                "image_coordinates": image,
                "coordinate_space": "shoulder_centered_normalized_3d",
                "entity_placement": {
                    "origin": relative,
                    "relative_to": "signer_shoulder_midpoint",
                },
            }
        return {
            "coordinates": image,
            "image_coordinates": image,
            "coordinate_space": "image_normalized_relative_depth",
            "entity_placement": {"origin": image, "relative_to": "image_frame"},
        }

    def _anchor(self, prior: list[dict[str, Any]], frames: list[dict[str, Any]]) -> dict[str, Any]:
        candidates: list[tuple[str, str, float]] = []
        for frame in [*prior, *frames]:
            for key in ("anchor_noun", "noun", "recognized_gloss", "gloss", "lexical_token"):
                value = frame.get(key)
                if isinstance(value, str) and value.strip():
                    source = "noun_metadata" if key in ("anchor_noun", "noun") else "recognized_gloss"
                    candidates.append((value.strip().upper(), source, 0.8 if source == "noun_metadata" else 0.65))
            for key in ("fingerspelled", "fingerspell"):
                value = frame.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append((value.strip().upper(), "fingerspelled", 0.75))
        if not candidates:
            return {"value": None, "source": "not_provided", "confidence": 0.0}
        value, source, confidence = candidates[-1]
        return {"value": value, "source": source, "confidence": confidence}

    def _non_manual_markers(self, frames: list[dict[str, Any]]) -> dict[str, Any]:
        brow_states: list[str] = []
        tilt_values: list[float] = []
        pitch_values: list[float] = []
        yaw_values: list[float] = []
        expressions: list[str] = []
        gaze_values: list[Any] = []
        for frame in frames:
            face = frame.get("face_expression") or frame.get("face") or {}
            if not isinstance(face, dict):
                continue
            brow_states.append(self._brow_state(face.get("blendshapes", {})))
            tilt_values.append(_number(face.get("head_roll", face.get("head_tilt"))))
            pitch_values.append(_number(face.get("head_pitch")))
            yaw_values.append(_number(face.get("head_yaw")))
            label = face.get("label") or face.get("expression")
            if isinstance(label, str) and label:
                expressions.append(label.upper())
            if face.get("gaze") is not None:
                gaze_values.append(face.get("gaze"))
        roll = median(tilt_values) if tilt_values else 0.0
        return {
            "brow_state": Counter(brow_states).most_common(1)[0][0] if brow_states else "UNKNOWN",
            "head_tilt": "LEFT" if roll < -0.12 else "RIGHT" if roll > 0.12 else "NEUTRAL",
            "head_roll": round(roll, 6),
            "head_pitch": round(median(pitch_values), 6) if pitch_values else 0.0,
            "head_yaw": round(median(yaw_values), 6) if yaw_values else 0.0,
            "eye_gaze": gaze_values[-1] if gaze_values else "UNKNOWN",
            "expression_label": Counter(expressions).most_common(1)[0][0] if expressions else "NONE",
            "synchronized_frames": len(frames),
        }

    @staticmethod
    def _brow_state(blendshapes: Any) -> str:
        if not isinstance(blendshapes, dict):
            return "UNKNOWN"
        up = max(_number(blendshapes.get(name)) for name in ("browInnerUp", "browOuterUpLeft", "browOuterUpRight"))
        down = max(_number(blendshapes.get(name)) for name in ("browDownLeft", "browDownRight"))
        if up >= 0.35 and up > down:
            return "RAISED"
        if down >= 0.35 and down > up:
            return "FURROWED"
        return "NEUTRAL"
