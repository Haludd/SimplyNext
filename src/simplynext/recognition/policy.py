"""Fail-closed confidence policy for turning hypotheses into user-visible actions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from .types import RecognitionCandidate, RecognitionResult


class DecisionStatus(StrEnum):
    CONFIDENT = "confident"
    REPAIR_REQUIRED = "repair_required"


class RepairAction(StrEnum):
    """Actions the UI can present without inventing a caption."""

    REPEAT = "repeat"
    CHOOSE_CANDIDATE = "choose_candidate"
    FINGERSPELL = "fingerspell"
    REPOSITION = "reposition"
    RECONNECT = "reconnect"
    MODEL_UNAVAILABLE = "model_unavailable"


@dataclass(frozen=True, slots=True)
class RecognitionQuality:
    """Capture and transport quality known outside the classifier."""

    coverage: float
    duration_ms: int | None
    received_frames: int
    dropped_frames: int = 0

    def __post_init__(self) -> None:
        if not math.isfinite(self.coverage) or not 0.0 <= self.coverage <= 1.0:
            raise ValueError("coverage must be between 0 and 1")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.received_frames < 0 or self.dropped_frames < 0:
            raise ValueError("frame counts must be non-negative")

    @property
    def dropped_fraction(self) -> float:
        attempted = self.received_frames + self.dropped_frames
        return self.dropped_frames / attempted if attempted else 0.0

    @classmethod
    def from_result(
        cls,
        result: RecognitionResult,
        *,
        dropped_frames: int = 0,
    ) -> RecognitionQuality:
        return cls(
            coverage=result.input_coverage,
            duration_ms=result.duration_ms,
            received_frames=result.frame_count,
            dropped_frames=dropped_frames,
        )


@dataclass(frozen=True, slots=True)
class ConfidenceThresholds:
    min_top1_confidence: float = 0.80
    min_top1_top2_margin: float = 0.15
    min_candidate_choice_confidence: float = 0.50
    min_coverage: float = 0.75
    min_duration_ms: int = 200
    max_duration_ms: int = 6_000
    max_dropped_fraction: float = 0.15
    require_calibrated: bool = True
    rejected_glosses: frozenset[str] = frozenset(
        {"UNKNOWN", "OOV", "NO_SIGN", "NO-SIGN", "TRANSITION", "<BLANK>"}
    )

    def __post_init__(self) -> None:
        unit_values = (
            self.min_top1_confidence,
            self.min_top1_top2_margin,
            self.min_candidate_choice_confidence,
            self.min_coverage,
            self.max_dropped_fraction,
        )
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in unit_values):
            raise ValueError("confidence policy fractions must be between 0 and 1")
        if self.min_duration_ms < 0 or self.max_duration_ms < self.min_duration_ms:
            raise ValueError("duration bounds are invalid")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """The only output that downstream caption assembly should consume."""

    status: DecisionStatus
    accepted: RecognitionCandidate | None
    repair_action: RepairAction | None
    reason_codes: tuple[str, ...]
    choices: tuple[RecognitionCandidate, ...] = ()

    @property
    def is_confident(self) -> bool:
        return self.status is DecisionStatus.CONFIDENT


class ConfidencePolicy:
    """Apply quality, calibration, vocabulary and ambiguity gates in a fixed order."""

    def __init__(self, thresholds: ConfidenceThresholds | None = None) -> None:
        self.thresholds = thresholds or ConfidenceThresholds()

    def evaluate(
        self,
        result: RecognitionResult,
        quality: RecognitionQuality | None = None,
    ) -> PolicyDecision:
        quality = quality or RecognitionQuality.from_result(result)
        thresholds = self.thresholds

        if not result.metadata.ready:
            return _repair(
                RepairAction.MODEL_UNAVAILABLE,
                *(result.metadata.issues or ("recognizer_not_ready",)),
            )
        if thresholds.require_calibrated and not result.metadata.calibrated:
            return _repair(
                RepairAction.MODEL_UNAVAILABLE,
                "confidence_not_calibrated",
            )
        if not result.candidates:
            return _repair(RepairAction.REPEAT, "no_hypotheses")

        top = result.candidates[0]
        canonical_gloss = _canonical_gloss(top.gloss)
        vocabulary = {_canonical_gloss(gloss) for gloss in result.metadata.vocabulary}
        if canonical_gloss in {_canonical_gloss(value) for value in thresholds.rejected_glosses}:
            action = (
                RepairAction.FINGERSPELL
                if canonical_gloss in {"UNKNOWN", "OOV"}
                else RepairAction.REPEAT
            )
            return _repair(action, f"rejected_class:{canonical_gloss.lower()}")
        if not vocabulary or canonical_gloss not in vocabulary:
            return _repair(RepairAction.FINGERSPELL, "out_of_vocabulary")

        if quality.coverage < thresholds.min_coverage:
            return _repair(RepairAction.REPOSITION, "insufficient_landmark_coverage")
        if quality.duration_ms is None:
            return _repair(RepairAction.REPEAT, "duration_unavailable")
        if quality.duration_ms < thresholds.min_duration_ms:
            return _repair(RepairAction.REPEAT, "utterance_too_short")
        if quality.duration_ms > thresholds.max_duration_ms:
            return _repair(RepairAction.REPEAT, "utterance_too_long")
        if quality.dropped_fraction > thresholds.max_dropped_fraction:
            return _repair(RepairAction.RECONNECT, "too_many_dropped_frames")

        second = result.candidates[1] if len(result.candidates) > 1 else None
        if top.confidence < thresholds.min_top1_confidence:
            choices = _viable_choices(result, thresholds.min_candidate_choice_confidence)
            if len(choices) >= 2:
                return _repair(
                    RepairAction.CHOOSE_CANDIDATE,
                    "top_confidence_below_threshold",
                    choices=choices,
                )
            return _repair(RepairAction.REPEAT, "top_confidence_below_threshold")

        if second is not None:
            margin = top.confidence - second.confidence
            if margin < thresholds.min_top1_top2_margin:
                choices = _viable_choices(
                    result,
                    thresholds.min_candidate_choice_confidence,
                )[:2]
                return (
                    _repair(
                        RepairAction.CHOOSE_CANDIDATE,
                        "top_candidates_ambiguous",
                        choices=choices,
                    )
                    if len(choices) >= 2
                    else _repair(RepairAction.REPEAT, "top_candidates_ambiguous")
                )

        return PolicyDecision(
            status=DecisionStatus.CONFIDENT,
            accepted=top,
            repair_action=None,
            reason_codes=(),
        )


def _canonical_gloss(gloss: str) -> str:
    return gloss.strip().upper().replace(" ", "_")


def _viable_choices(
    result: RecognitionResult,
    minimum_confidence: float,
) -> tuple[RecognitionCandidate, ...]:
    return tuple(
        candidate for candidate in result.candidates if candidate.confidence >= minimum_confidence
    )


def _repair(
    action: RepairAction,
    *reason_codes: str,
    choices: tuple[RecognitionCandidate, ...] = (),
) -> PolicyDecision:
    return PolicyDecision(
        status=DecisionStatus.REPAIR_REQUIRED,
        accepted=None,
        repair_action=action,
        reason_codes=tuple(reason_codes),
        choices=choices,
    )
