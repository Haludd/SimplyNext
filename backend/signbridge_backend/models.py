"""Validation and typed access for the Flutter sign-sequence contract."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


class PayloadValidationError(ValueError):
    """Raised when a client sends a malformed or unsafe sequence payload."""


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _required_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise PayloadValidationError(f"{field} must be a list")
    return value


def _finite_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise PayloadValidationError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise PayloadValidationError(f"{field} must be finite")
    return result


def _validate_landmarks(frame_index: int, hand_index: int, hand: dict[str, Any]) -> None:
    landmarks = _required_list(
        hand.get("landmarks", []),
        f"frames[{frame_index}].hands[{hand_index}].landmarks",
    )
    if len(landmarks) not in (0, 21):
        raise PayloadValidationError(
            f"frames[{frame_index}].hands[{hand_index}].landmarks must contain 21 points"
        )
    for point_index, point in enumerate(landmarks):
        if not isinstance(point, dict):
            raise PayloadValidationError(
                f"frames[{frame_index}].hands[{hand_index}].landmarks[{point_index}] must be an object"
            )
        for axis in ("x", "y", "z"):
            _finite_number(
                point.get(axis),
                f"frames[{frame_index}].hands[{hand_index}].landmarks[{point_index}].{axis}",
            )
        for axis in ("world_x", "world_y", "world_z"):
            if axis in point and point[axis] is not None:
                _finite_number(
                    point[axis],
                    f"frames[{frame_index}].hands[{hand_index}].landmarks[{point_index}].{axis}",
                )


def _validate_frame(index: int, frame: Any) -> None:
    if not isinstance(frame, dict):
        raise PayloadValidationError(f"frames[{index}] must be an object")
    _required_string(frame.get("timestamp"), f"frames[{index}].timestamp")
    confidence = frame.get("tracking_confidence", 0)
    _finite_number(confidence, f"frames[{index}].tracking_confidence")

    hands = _required_list(frame.get("hands", []), f"frames[{index}].hands")
    if len(hands) > 2:
        raise PayloadValidationError(f"frames[{index}].hands cannot contain more than 2 hands")
    for hand_index, hand in enumerate(hands):
        if not isinstance(hand, dict):
            raise PayloadValidationError(f"frames[{index}].hands[{hand_index}] must be an object")
        _required_string(hand.get("handedness", "unknown"), f"frames[{index}].hands[{hand_index}].handedness")
        _finite_number(hand.get("confidence", 0), f"frames[{index}].hands[{hand_index}].confidence")
        _validate_landmarks(index, hand_index, hand)

    face = frame.get("face_expression")
    if face is not None:
        if not isinstance(face, dict):
            raise PayloadValidationError(f"frames[{index}].face_expression must be an object")
        if "confidence" in face:
            _finite_number(face["confidence"], f"frames[{index}].face_expression.confidence")
        if "label" in face and face["label"] is not None:
            _required_string(face["label"], f"frames[{index}].face_expression.label")


def _optional_face_analysis(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise PayloadValidationError("face_analysis must be an object")
    return value


@dataclass(frozen=True)
class SignSequencePayload:
    """Validated representation of the JSON emitted by the Flutter client."""

    session_id: str
    sequence_id: str
    language: str
    started_at: str
    ended_at: str
    frame_count: int
    lexicon_version: str
    frames: list[dict[str, Any]]
    face_analysis: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, value: Any) -> "SignSequencePayload":
        if not isinstance(value, dict):
            raise PayloadValidationError("request body must be a JSON object")

        session_id = _required_string(value.get("session_id"), "session_id")
        sequence_id = _required_string(value.get("sequence_id"), "sequence_id")
        language = _required_string(value.get("language"), "language").upper()
        started_at = _required_string(value.get("started_at"), "started_at")
        ended_at = _required_string(value.get("ended_at"), "ended_at")
        lexicon_version = _required_string(value.get("lexicon_version"), "lexicon_version")
        frames = _required_list(value.get("frames"), "frames")
        if not frames:
            raise PayloadValidationError("frames must contain at least one frame")
        if len(frames) > 600:
            raise PayloadValidationError("frames cannot contain more than 600 frames")
        for index, frame in enumerate(frames):
            _validate_frame(index, frame)

        frame_count = value.get("frame_count")
        if not isinstance(frame_count, int) or isinstance(frame_count, bool):
            raise PayloadValidationError("frame_count must be an integer")
        if frame_count != len(frames):
            raise PayloadValidationError("frame_count must equal the number of frames")

        return cls(
            session_id=session_id,
            sequence_id=sequence_id,
            language=language,
            started_at=started_at,
            ended_at=ended_at,
            frame_count=frame_count,
            lexicon_version=lexicon_version,
            frames=frames,
            face_analysis=_optional_face_analysis(value.get("face_analysis")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "sequence_id": self.sequence_id,
            "language": self.language,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "frame_count": self.frame_count,
            "lexicon_version": self.lexicon_version,
            "frames": self.frames,
            **({"face_analysis": self.face_analysis} if self.face_analysis else {}),
        }
