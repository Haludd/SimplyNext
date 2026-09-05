from __future__ import annotations

import pytest

from simplynext.recognition import (
    ConfidencePolicy,
    DecisionStatus,
    RecognitionCandidate,
    RecognitionMetadata,
    RecognitionQuality,
    RecognitionResult,
    RepairAction,
)


def _result(
    *candidates: RecognitionCandidate,
    calibrated: bool = True,
    ready: bool = True,
    vocabulary: tuple[str, ...] = ("HELLO", "BYE", "NO_SIGN", "UNKNOWN"),
) -> RecognitionResult:
    return RecognitionResult(
        candidates=tuple(candidates),
        metadata=RecognitionMetadata(
            ready=ready,
            calibrated=calibrated,
            schema_version=1,
            model_version="test-v1",
            vocabulary=vocabulary,
            template_count=4,
            feature_names=("x",),
            issues=() if ready else ("recognizer_unconfigured",),
        ),
        input_coverage=0.95,
        frame_count=20,
        duration_ms=700,
    )


def _candidate(gloss: str, confidence: float) -> RecognitionCandidate:
    return RecognitionCandidate(gloss=gloss, confidence=confidence, distance=0.1)


def test_policy_accepts_only_a_calibrated_clear_winner() -> None:
    decision = ConfidencePolicy().evaluate(
        _result(_candidate("HELLO", 0.95), _candidate("BYE", 0.60))
    )

    assert decision.status is DecisionStatus.CONFIDENT
    assert decision.accepted is not None
    assert decision.accepted.gloss == "HELLO"
    assert decision.repair_action is None


@pytest.mark.parametrize(
    ("result", "action", "reason"),
    [
        (
            _result(_candidate("HELLO", 0.99), ready=False),
            RepairAction.MODEL_UNAVAILABLE,
            "recognizer_unconfigured",
        ),
        (
            _result(_candidate("HELLO", 0.99), calibrated=False),
            RepairAction.MODEL_UNAVAILABLE,
            "confidence_not_calibrated",
        ),
        (
            _result(_candidate("NO_SIGN", 0.99)),
            RepairAction.REPEAT,
            "rejected_class:no_sign",
        ),
        (
            _result(_candidate("UNKNOWN", 0.99)),
            RepairAction.FINGERSPELL,
            "rejected_class:unknown",
        ),
        (
            _result(_candidate("NEW_GLOSS", 0.99)),
            RepairAction.FINGERSPELL,
            "out_of_vocabulary",
        ),
    ],
)
def test_policy_special_classes_and_readiness_fail_closed(
    result: RecognitionResult,
    action: RepairAction,
    reason: str,
) -> None:
    decision = ConfidencePolicy().evaluate(result)

    assert decision.status is DecisionStatus.REPAIR_REQUIRED
    assert decision.accepted is None
    assert decision.repair_action is action
    assert reason in decision.reason_codes


def test_policy_offers_candidates_only_when_two_are_viable() -> None:
    result = _result(_candidate("HELLO", 0.78), _candidate("BYE", 0.72))

    decision = ConfidencePolicy().evaluate(result)

    assert decision.repair_action is RepairAction.CHOOSE_CANDIDATE
    assert [choice.gloss for choice in decision.choices] == ["HELLO", "BYE"]


def test_policy_rejects_small_top_two_margin() -> None:
    result = _result(_candidate("HELLO", 0.93), _candidate("BYE", 0.85))

    decision = ConfidencePolicy().evaluate(result)

    assert decision.repair_action is RepairAction.CHOOSE_CANDIDATE
    assert decision.reason_codes == ("top_candidates_ambiguous",)


def test_policy_prefers_capture_repair_before_confidence() -> None:
    result = _result(_candidate("HELLO", 0.40), _candidate("BYE", 0.20))
    quality = RecognitionQuality(
        coverage=0.40,
        duration_ms=700,
        received_frames=20,
    )

    decision = ConfidencePolicy().evaluate(result, quality)

    assert decision.repair_action is RepairAction.REPOSITION
    assert decision.reason_codes == ("insufficient_landmark_coverage",)


def test_policy_rejects_excess_transport_loss() -> None:
    result = _result(_candidate("HELLO", 0.95), _candidate("BYE", 0.50))
    quality = RecognitionQuality(
        coverage=0.95,
        duration_ms=700,
        received_frames=80,
        dropped_frames=20,
    )

    decision = ConfidencePolicy().evaluate(result, quality)

    assert decision.repair_action is RepairAction.RECONNECT
    assert decision.reason_codes == ("too_many_dropped_frames",)


def test_quality_can_be_derived_from_recognition_result() -> None:
    result = _result(_candidate("HELLO", 0.95), _candidate("BYE", 0.50))

    quality = RecognitionQuality.from_result(result, dropped_frames=2)

    assert quality.coverage == 0.95
    assert quality.duration_ms == 700
    assert quality.dropped_fraction == pytest.approx(2 / 22)
