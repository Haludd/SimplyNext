"""Replaceable baseline analyzer for hand, motion, and face features."""

from __future__ import annotations

import math
from typing import Any

from .models import SignSequencePayload


class SignAnalyzer:
    """A safe closed-vocabulary baseline until a trained model is available.

    This intentionally returns a candidate handshape instead of pretending that
    a few geometric thresholds are a complete ASL translator. A trained
    sequence model can implement the same ``analyze`` method later.
    """

    def __init__(self, model_version: str = "heuristic-signbridge-v1") -> None:
        self.model_version = model_version

    def analyze(self, payload: SignSequencePayload) -> dict[str, Any]:
        tracked_frames = [
            frame for frame in payload.frames if frame.get("hands")
        ]
        if not tracked_frames:
            return {
                "status": "no_signal",
                "gesture_label": "No hand signal",
                "caption": "Show your hands to begin tracking.",
                "confidence": 0.0,
                "gloss_trace": [],
                "detail": "No hand landmarks were present in the sequence.",
                "model_version": self.model_version,
                "language": payload.language,
            }

        latest = tracked_frames[-1]
        hands = latest.get("hands", [])
        openness_values = [self._hand_openness(hand) for hand in hands]
        openness_values = [value for value in openness_values if value is not None]
        motion = latest.get("hand_motion") or {}
        openness = (
            sum(openness_values) / len(openness_values)
            if openness_values
            else float(motion.get("average_openness", 0.0) or 0.0)
        )
        speed = float(motion.get("average_speed", 0.0) or 0.0)
        label = self._gesture_label(openness)
        tracking_confidence = float(latest.get("tracking_confidence", 0.0) or 0.0)
        confidence = max(0.0, min(0.99, tracking_confidence * 0.65 + (0.35 if openness > 0.1 else 0.12)))
        face = latest.get("face_expression") or {}
        face_label = str(face.get("label", "not detected"))

        return {
            "status": "candidate",
            "gesture_label": label,
            "caption": "Hand sequence captured — review candidate before translation.",
            "confidence": round(confidence, 4),
            "gloss_trace": [label.upper()],
            "detail": (
                f"{len(tracked_frames)} frames · {len(hands)} hand(s) · "
                f"{speed:.2f} motion · face {face_label} · "
                "heuristic baseline, not a trained ASL translation model."
            ),
            "model_version": self.model_version,
            "language": payload.language,
        }

    def _gesture_label(self, openness: float) -> str:
        if openness >= 0.8:
            return "open hand"
        if openness <= 0.2:
            return "closed hand"
        if 0.35 <= openness <= 0.5:
            return "partial handshape"
        return "unknown handshape"

    def _hand_openness(self, hand: dict[str, Any]) -> float | None:
        landmarks = hand.get("landmarks", [])
        if len(landmarks) < 21:
            return None
        wrist = landmarks[0]
        tips = (4, 8, 12, 16, 20)
        mcps = (2, 5, 9, 13, 17)
        extended = 0
        for tip_index, mcp_index in zip(tips, mcps):
            if self._distance(landmarks[tip_index], wrist) > self._distance(landmarks[mcp_index], wrist) * 1.18:
                extended += 1
        return extended / len(tips)

    @staticmethod
    def _distance(first: dict[str, Any], second: dict[str, Any]) -> float:
        return math.sqrt(
            sum(
                (float(first[axis]) - float(second[axis])) ** 2
                for axis in ("x", "y", "z")
            )
        )
