from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from simplynext.agent import (
    AssemblyRequest,
    AssemblyResult,
    CaptionTemplate,
    DeterministicTemplateAssembler,
)
from simplynext.contracts import (
    GlossHypothesis,
    LandmarkFrame,
    RepairAction,
    RepairRequiredEvent,
    SignLanguage,
    TranslationStatus,
    UtteranceRequest,
)
from simplynext.observability import MetricsRegistry
from simplynext.orchestrator import TranslationEngine
from simplynext.recognition import (
    ConfidencePolicy,
    RecognitionCandidate,
    RecognitionMetadata,
    RecognitionResult,
    UnconfiguredRecognizer,
)


def _request(*, calibrated: bool) -> UtteranceRequest:
    started_at = datetime(2026, 9, 5, 4, 0, tzinfo=UTC)
    return UtteranceRequest(
        session_id="session-123",
        utterance_id="utt-008",
        language=SignLanguage.ASL,
        started_at=started_at,
        ended_at=started_at + timedelta(milliseconds=700),
        hypotheses=(
            GlossHypothesis(gloss="HELLO", confidence=0.96),
            GlossHypothesis(gloss="BYE", confidence=0.40),
        ),
        features={
            "calibrated": calibrated,
            "model_version": "client-demo-v1",
            "frame_count": 20,
            "dropped_frames": 0,
            "landmark_coverage": 0.95,
        },
    )


def _engine(*, recognizer=None, assembler=None) -> tuple[TranslationEngine, MetricsRegistry]:
    metrics = MetricsRegistry()
    return (
        TranslationEngine(
            recognizer=recognizer or UnconfiguredRecognizer(),
            policy=ConfidencePolicy(),
            assembler=assembler
            or DeterministicTemplateAssembler({("HELLO",): CaptionTemplate("Hello.")}),
            metrics=metrics,
        ),
        metrics,
    )


def test_calibrated_http_hypothesis_uses_only_the_exact_caption_template() -> None:
    engine, metrics = _engine()

    result = asyncio.run(engine.process_hypotheses(_request(calibrated=True)))

    assert result.status is TranslationStatus.CONFIDENT
    assert result.caption == "Hello."
    assert result.tts_text == "Hello."
    assert result.gloss_trace == ("HELLO",)
    assert result.confidence == 0.96
    assert result.model_version == "client-demo-v1"
    assert result.repair_action is None
    assert metrics.snapshot()["counters"] == {"utterances_confident": 1}


class _AssemblerMustNotRun:
    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        raise AssertionError(f"assembler received rejected evidence for {request.utterance_id}")


def test_uncalibrated_http_hypothesis_is_rejected_before_assembly() -> None:
    engine, _ = _engine(assembler=_AssemblerMustNotRun())

    result = asyncio.run(engine.process_hypotheses(_request(calibrated=False)))

    assert result.status is TranslationStatus.UNCERTAIN
    assert result.caption is None
    assert result.tts_text is None
    assert result.repair_action is RepairAction.MODEL_UNAVAILABLE
    assert result.reason_codes == ("confidence_not_calibrated",)
    assert result.message == "Recognition is not configured yet."


def test_unusable_frame_window_fails_closed_with_reposition_repair() -> None:
    engine, metrics = _engine()
    frames = (
        LandmarkFrame(seq=10, capture_ms=1_000),
        LandmarkFrame(seq=11, capture_ms=1_050),
    )

    result = asyncio.run(
        engine.process_frames(
            utterance_id="utt-frames-1",
            language=SignLanguage.ASL,
            frames=frames,
        )
    )

    assert isinstance(result, RepairRequiredEvent)
    assert result.status == "uncertain"
    assert result.action is RepairAction.REPOSITION
    assert result.confidence == 0.0
    assert result.reason_codes == ("normalization_failed",)
    assert "caption" not in result.model_dump()
    assert metrics.snapshot()["counters"] == {"utterances_repair_required": 1}


def _valid_frames() -> tuple[LandmarkFrame, LandmarkFrame]:
    pose = (
        (0.5, 0.3, 0.0, 1.0),
        (0.4, 0.5, 0.0, 1.0),
        (0.6, 0.5, 0.0, 1.0),
        (0.35, 0.6, 0.0, 1.0),
        (0.65, 0.6, 0.0, 1.0),
        (0.32, 0.45, 0.0, 1.0),
        (0.68, 0.45, 0.0, 1.0),
        (0.44, 0.8, 0.0, 1.0),
        (0.56, 0.8, 0.0, 1.0),
    )
    left_hand = tuple((0.32 + index * 0.003, 0.45 - index * 0.004, 0.0, 1.0) for index in range(21))
    return (
        LandmarkFrame(seq=20, capture_ms=2_000, pose=pose, left_hand=left_hand),
        LandmarkFrame(seq=21, capture_ms=2_100, pose=pose, left_hand=left_hand),
    )


class _RaisingRecognizer:
    metadata = RecognitionMetadata(
        ready=True,
        calibrated=True,
        schema_version=1,
        model_version="raising-v1",
        vocabulary=("HELLO",),
    )

    def recognize(self, sequence, *, top_k: int = 3) -> RecognitionResult:
        raise RuntimeError("simulated recognition failure")


class _AcceptingRecognizer:
    metadata = RecognitionMetadata(
        ready=True,
        calibrated=True,
        schema_version=1,
        model_version="accepting-v1",
        vocabulary=("HELLO", "BYE"),
    )

    def recognize(self, sequence, *, top_k: int = 3) -> RecognitionResult:
        return RecognitionResult(
            candidates=(
                RecognitionCandidate("HELLO", 0.96),
                RecognitionCandidate("BYE", 0.40),
            ),
            metadata=self.metadata,
            input_coverage=0.95,
            frame_count=32,
            duration_ms=700,
        )


class _RaisingAssembler:
    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        raise RuntimeError("simulated assembly failure")


def test_recognizer_exception_fails_closed_and_records_repair_metric() -> None:
    engine, metrics = _engine(recognizer=_RaisingRecognizer())

    result = asyncio.run(
        engine.process_frames(
            utterance_id="utt-recognizer-failure",
            language=SignLanguage.ASL,
            frames=_valid_frames(),
        )
    )

    assert isinstance(result, RepairRequiredEvent)
    assert result.action is RepairAction.MODEL_UNAVAILABLE
    assert result.confidence == 0.0
    assert result.reason_codes == ("recognition_failed",)
    assert result.model_version == "raising-v1"
    assert "caption" not in result.model_dump()
    assert metrics.snapshot()["counters"] == {"utterances_repair_required": 1}


def test_assembler_exception_fails_closed_and_records_repair_metric() -> None:
    engine, metrics = _engine(
        recognizer=_AcceptingRecognizer(),
        assembler=_RaisingAssembler(),
    )

    result = asyncio.run(
        engine.process_frames(
            utterance_id="utt-assembler-failure",
            language=SignLanguage.ASL,
            frames=_valid_frames(),
        )
    )

    assert isinstance(result, RepairRequiredEvent)
    assert result.action is RepairAction.ESCALATE
    assert result.confidence == 0.96
    assert result.reason_codes == ("assembly_failed",)
    assert result.model_version == "accepting-v1"
    assert "caption" not in result.model_dump()
    assert metrics.snapshot()["counters"] == {"utterances_repair_required": 1}


def test_transport_loss_uses_raw_frame_count_not_resampled_frame_count() -> None:
    engine, _ = _engine(recognizer=_AcceptingRecognizer())

    result = asyncio.run(
        engine.process_frames(
            utterance_id="utt-raw-frame-loss",
            language=SignLanguage.ASL,
            frames=_valid_frames(),
            dropped_frames=1,
        )
    )

    assert isinstance(result, RepairRequiredEvent)
    assert result.action is RepairAction.RECONNECT
    assert result.reason_codes == ("too_many_dropped_frames",)
