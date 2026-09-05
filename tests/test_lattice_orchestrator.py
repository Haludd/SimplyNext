from __future__ import annotations

import asyncio

from simplynext.agent import AssemblyRequest, AssemblyResult, AssemblyStatus
from simplynext.contracts import (
    ClassifierDescriptor,
    GlossCandidate,
    GlossLattice,
    GlossLatticeProducer,
    GlossLatticeQuality,
    GlossLatticeSlot,
    GlossProvenance,
    LatticeRepairRequiredEvent,
    LatticeResultEvent,
    RepairAction,
    SignLanguage,
)
from simplynext.observability import MetricsRegistry
from simplynext.orchestrator import TranslationEngine
from simplynext.recognition import ConfidencePolicy, UnconfiguredRecognizer


def classifier() -> ClassifierDescriptor:
    return ClassifierDescriptor(
        name="temporal-classifier",
        model_version="asl-demo-v3",
        calibration_version="temperature-v2",
        vocabulary_version="demo-v1",
    )


def candidate(rank: int, gloss: str, confidence: float) -> GlossCandidate:
    return GlossCandidate(rank=rank, gloss=gloss, confidence=confidence)


def slot(
    slot_id: str,
    start_ms: int,
    end_ms: int,
    *,
    candidates: tuple[GlossCandidate, ...],
    resolved_gloss: str | None,
    selected_rank: int | None,
    provenance: GlossProvenance,
    confirmed_at_ms: int | None = None,
    reason_codes: tuple[str, ...] = (),
) -> GlossLatticeSlot:
    return GlossLatticeSlot(
        slot_id=slot_id,
        start_ms=start_ms,
        end_ms=end_ms,
        candidates=candidates,
        resolved_gloss=resolved_gloss,
        selected_rank=selected_rank,
        provenance=provenance,
        confirmed_at_ms=confirmed_at_ms,
        reason_codes=reason_codes,
    )


def lattice(
    *slots: GlossLatticeSlot,
    is_final: bool = True,
    quality: GlossLatticeQuality | None = None,
) -> GlossLattice:
    return GlossLattice(
        session_id="12345678-1234-5678-1234-567812345678",
        lattice_seq=4,
        utterance_id="utt-004",
        language=SignLanguage.ASL,
        subject_id="signer-a",
        is_final=is_final,
        capture_start_ms=1_000,
        capture_end_ms=1_800,
        produced_ms=1_850,
        producer=GlossLatticeProducer(
            classifier=classifier(),
            segmenter_version="segmenter-v2",
            top_k=3,
        ),
        quality=quality,
        slots=slots,
    )


class SpyAssembler:
    def __init__(self) -> None:
        self.requests: list[AssemblyRequest] = []

    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        self.requests.append(request)
        return AssemblyResult(
            utterance_id=request.utterance_id,
            status=AssemblyStatus.CONFIDENT,
            caption="Hello, please.",
            tts_text="Hello, please.",
            gloss_trace=request.evidence,
            confidence=min(item.confidence for item in request.evidence),
            source="spy_agent",
        )


class MustNotRunAssembler:
    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        raise AssertionError(f"Agent received unsafe lattice {request.utterance_id}")


class RaisingAssembler:
    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        raise RuntimeError(f"simulated failure for {request.utterance_id}")


def engine(assembler) -> tuple[TranslationEngine, MetricsRegistry]:
    metrics = MetricsRegistry()
    return (
        TranslationEngine(
            recognizer=UnconfiguredRecognizer(),
            policy=ConfidencePolicy(),
            assembler=assembler,
            metrics=metrics,
            model_language=SignLanguage.ASL,
        ),
        metrics,
    )


def resolved_lattice() -> GlossLattice:
    return lattice(
        slot(
            "s0",
            1_000,
            1_300,
            candidates=(
                candidate(1, "HELLO", 0.96),
                candidate(2, "WELCOME", 0.20),
                candidate(3, "BYE", 0.05),
            ),
            resolved_gloss="HELLO",
            selected_rank=1,
            provenance=GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
        ),
        slot(
            "s1",
            1_350,
            1_800,
            candidates=(
                candidate(1, "THANK_YOU", 0.55),
                candidate(2, "PLEASE", 0.42),
                candidate(3, "SORRY", 0.03),
            ),
            resolved_gloss="PLEASE",
            selected_rank=2,
            provenance=GlossProvenance.TOP_K_SIGNER_CONFIRMED,
            confirmed_at_ms=1_840,
        ),
    )


def test_complete_lattice_reaches_agent_without_top_k_collapse() -> None:
    assembler = SpyAssembler()
    translation, metrics = engine(assembler)

    result = asyncio.run(translation.process_lattice(resolved_lattice()))

    assert isinstance(result, LatticeResultEvent)
    assert result.caption == "Hello, please."
    assert result.gloss_trace == ("HELLO", "PLEASE")
    assert [item.provenance for item in result.evidence_trace] == [
        GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
        GlossProvenance.TOP_K_SIGNER_CONFIRMED,
    ]
    assert len(assembler.requests) == 1
    request = assembler.requests[0]
    assert request.lattice == resolved_lattice()
    assert request.lattice_seq == 4
    assert request.revision == 0
    assert request.subject_id == "signer-a"
    assert request.calibration_version == "temperature-v2"
    assert [[item.gloss for item in evidence.alternatives] for evidence in request.evidence] == [
        ["HELLO", "WELCOME", "BYE"],
        ["THANK_YOU", "PLEASE", "SORRY"],
    ]
    assert [(item.start_ms, item.end_ms) for item in request.evidence] == [
        (1_000, 1_300),
        (1_350, 1_800),
    ]
    counters = metrics.snapshot()["counters"]
    assert counters["lattice_utterances_confident"] == 1
    assert counters["lattice_provenance_classifier_high_confidence"] == 1
    assert counters["lattice_provenance_top_k_signer_confirmed"] == 1


def test_unresolved_slot_returns_slot_scoped_choices_without_running_agent() -> None:
    translation, _ = engine(MustNotRunAssembler())
    payload = lattice(
        slot(
            "gap-1",
            1_000,
            1_800,
            candidates=(
                candidate(1, "WATER", 0.54),
                candidate(2, "DRINK", 0.49),
            ),
            resolved_gloss=None,
            selected_rank=None,
            provenance=GlossProvenance.UNRESOLVED,
            reason_codes=("ambiguous_top_k",),
        )
    )

    result = asyncio.run(translation.process_lattice(payload))

    assert isinstance(result, LatticeRepairRequiredEvent)
    assert result.action is RepairAction.CHOOSE_CANDIDATE
    assert result.target_slot_ids == ("gap-1",)
    assert [(item.slot_id, item.gloss) for item in result.choices] == [
        ("gap-1", "WATER"),
        ("gap-1", "DRINK"),
    ]
    assert result.evidence_trace[0].resolved_gloss is None
    assert "caption" not in result.model_dump()
    assert "tts_text" not in result.model_dump()


def test_partial_lattice_never_runs_agent() -> None:
    translation, _ = engine(MustNotRunAssembler())
    payload = resolved_lattice().model_copy(update={"is_final": False})

    result = asyncio.run(translation.process_lattice(payload))

    assert isinstance(result, LatticeRepairRequiredEvent)
    assert result.action is RepairAction.REPEAT
    assert result.reason_codes == ("lattice_not_final",)


def test_false_high_confidence_provenance_is_rechecked_server_side() -> None:
    translation, _ = engine(MustNotRunAssembler())
    payload = lattice(
        slot(
            "s0",
            1_000,
            1_800,
            candidates=(
                candidate(1, "WATER", 0.74),
                candidate(2, "DRINK", 0.60),
            ),
            resolved_gloss="WATER",
            selected_rank=1,
            provenance=GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
        )
    )

    result = asyncio.run(translation.process_lattice(payload))

    assert isinstance(result, LatticeRepairRequiredEvent)
    assert result.action is RepairAction.CHOOSE_CANDIDATE
    assert result.reason_codes == ("classifier_provenance_below_threshold",)


def test_aggregate_frontend_quality_remains_a_fail_closed_gate() -> None:
    translation, _ = engine(MustNotRunAssembler())
    payload = lattice(
        *resolved_lattice().slots,
        quality=GlossLatticeQuality(
            observed_frames=20,
            dropped_frames=0,
            landmark_coverage=0.40,
            classifier_latency_ms=18,
        ),
    )

    result = asyncio.run(translation.process_lattice(payload))

    assert isinstance(result, LatticeRepairRequiredEvent)
    assert result.action is RepairAction.REPOSITION
    assert result.reason_codes == ("insufficient_landmark_coverage",)


def test_agent_exception_is_a_repair_and_never_model_text() -> None:
    translation, metrics = engine(RaisingAssembler())

    result = asyncio.run(translation.process_lattice(resolved_lattice()))

    assert isinstance(result, LatticeRepairRequiredEvent)
    assert result.action is RepairAction.ESCALATE
    assert result.reason_codes == ("assembly_failed",)
    assert result.agent_source is None
    assert "caption" not in result.model_dump()
    assert metrics.snapshot()["counters"]["lattice_utterances_repair_required"] == 1
