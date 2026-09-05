from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from simplynext.contracts import (
    GLOSS_LATTICE_SCHEMA_VERSION,
    MAX_GLOSS_LATTICE_BYTES,
    GlossCandidate,
    GlossLattice,
    GlossLatticeProducer,
    GlossProvenance,
    GlossSlot,
)

SESSION_ID = UUID("12345678-1234-5678-1234-567812345678")
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gloss_lattice_v1.json"


def candidate(gloss_id: str, rank: int, confidence: float) -> GlossCandidate:
    return GlossCandidate(gloss_id=gloss_id, rank=rank, confidence=confidence)


def slot(
    index: int,
    *,
    candidates: tuple[GlossCandidate, ...] | None = None,
    resolved_gloss_id: str | None = "WATER",
    provenance: GlossProvenance = GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
) -> GlossSlot:
    retained = candidates if candidates is not None else (candidate("WATER", 1, 0.96),)
    return GlossSlot(
        slot_index=index,
        slot_id=f"slot-{index}",
        start_ms=1_000 + index * 500,
        end_ms=1_400 + index * 500,
        candidates=retained,
        resolved_gloss_id=resolved_gloss_id,
        provenance=provenance,
    )


def producer() -> GlossLatticeProducer:
    return GlossLatticeProducer(
        classifier_id="temporal_classifier",
        classifier_version="1.3.0",
        confidence_kind="calibrated_probability",
        calibration_version="temperature_v2",
        vocabulary_version="sgsl_demo_v1",
    )


def lattice(*slots: GlossSlot) -> GlossLattice:
    retained_slots = slots or (slot(0),)
    return GlossLattice(
        type="gloss_lattice",
        schema_version=GLOSS_LATTICE_SCHEMA_VERSION,
        session_id=SESSION_ID,
        lattice_seq=7,
        utterance_id="utterance-42",
        language="sgsl",
        timebase="session_monotonic_ms",
        started_at_ms=900,
        ended_at_ms=1_000 + len(retained_slots) * 500,
        producer=producer(),
        slots=retained_slots,
    )


def test_lattice_round_trips_as_compact_versioned_json() -> None:
    original = lattice()
    payload = original.model_dump_json()
    restored = GlossLattice.model_validate_json(payload)

    assert restored == original
    assert restored.type == "gloss_lattice"
    assert restored.schema_version == "1.0"
    assert restored.timebase == "session_monotonic_ms"
    assert len(payload.encode("utf-8")) <= MAX_GLOSS_LATTICE_BYTES


def test_shared_v1_fixture_matches_the_runtime_contract() -> None:
    parsed = GlossLattice.model_validate_json(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert parsed.utterance_id == "utterance-42"
    assert tuple(slot.provenance for slot in parsed.slots) == tuple(GlossProvenance)
    assert len(parsed.model_dump_json().encode("utf-8")) <= MAX_GLOSS_LATTICE_BYTES


def test_each_provenance_rung_has_explicit_resolution_semantics() -> None:
    top_k = (
        candidate("WATER", 1, 0.55),
        candidate("WHAT", 2, 0.35),
    )
    confirmed = slot(
        0,
        candidates=top_k,
        resolved_gloss_id="WHAT",
        provenance=GlossProvenance.TOP_K_SIGNER_CONFIRMED,
    )
    fingerspelled = slot(
        0,
        candidates=(),
        resolved_gloss_id="J-O-H-N",
        provenance=GlossProvenance.FINGERSPELLED,
    )
    unresolved = slot(
        0,
        candidates=top_k,
        resolved_gloss_id=None,
        provenance=GlossProvenance.UNRESOLVED,
    )

    assert confirmed.resolved_gloss_id == "WHAT"
    assert fingerspelled.resolved_gloss_id == "J-O-H-N"
    assert unresolved.resolved_gloss_id is None

    with pytest.raises(ValidationError, match="rank-1"):
        slot(0, candidates=top_k, resolved_gloss_id="WHAT")
    with pytest.raises(ValidationError, match="cannot have"):
        slot(
            0,
            candidates=top_k,
            resolved_gloss_id="WATER",
            provenance=GlossProvenance.UNRESOLVED,
        )


def test_candidates_are_unique_contiguous_and_confidence_ordered() -> None:
    with pytest.raises(ValidationError, match="contiguous"):
        slot(
            0,
            candidates=(candidate("WATER", 1, 0.9), candidate("WHAT", 3, 0.8)),
        )
    with pytest.raises(ValidationError, match="unique"):
        slot(
            0,
            candidates=(candidate("WATER", 1, 0.9), candidate("WATER", 2, 0.8)),
        )
    with pytest.raises(ValidationError, match="non-increasing"):
        slot(
            0,
            candidates=(candidate("WATER", 1, 0.7), candidate("WHAT", 2, 0.8)),
        )


def test_slots_are_unique_contiguous_non_overlapping_and_in_range() -> None:
    first = slot(0)
    with pytest.raises(ValidationError, match="contiguous"):
        lattice(first, slot(2))

    overlapping = GlossSlot(
        **{
            **slot(1).model_dump(),
            "start_ms": first.end_ms - 1,
            "end_ms": first.end_ms + 100,
        }
    )
    with pytest.raises(ValidationError, match="non-overlapping"):
        lattice(first, overlapping)

    with pytest.raises(ValidationError, match="within"):
        GlossLattice(
            **{
                **lattice().model_dump(),
                "started_at_ms": first.start_ms + 1,
            }
        )


def test_contract_rejects_unknown_fields_and_landmark_payloads() -> None:
    payload = lattice().model_dump(mode="json")
    payload["frames"] = [{"pose": [[0.1, 0.2, 0.3, 0.9]]}]

    with pytest.raises(ValidationError, match="Extra inputs"):
        GlossLattice.model_validate(payload)
    with pytest.raises(ValidationError):
        GlossLattice.model_validate({**lattice().model_dump(), "schema_version": "2.0"})


@pytest.mark.parametrize("field", ("type", "schema_version", "timebase"))
def test_wire_discriminators_are_required(field: str) -> None:
    payload = lattice().model_dump()
    del payload[field]

    with pytest.raises(ValidationError):
        GlossLattice.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("lattice_seq", "7"),
        ("lattice_seq", True),
        ("started_at_ms", "900"),
        ("started_at_ms", False),
    ),
)
def test_contract_rejects_coerced_integer_fields(field: str, value: object) -> None:
    payload = lattice().model_dump()
    payload[field] = value

    with pytest.raises(ValidationError):
        GlossLattice.model_validate(payload)


def test_contract_rejects_coerced_candidate_values() -> None:
    with pytest.raises(ValidationError):
        candidate("WATER", True, 0.9)
    with pytest.raises(ValidationError):
        candidate("WATER", 1, "0.9")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        candidate(" WATER ", 1, 0.9)


def test_contract_rejects_lattice_over_fixed_byte_ceiling() -> None:
    oversized_slots = []
    for slot_index in range(64):
        hypotheses = tuple(
            candidate(
                f"G{slot_index:02d}_{rank}_" + "X" * 116,
                rank,
                1.0 - rank / 10,
            )
            for rank in range(1, 6)
        )
        oversized_slots.append(
            GlossSlot(
                slot_index=slot_index,
                slot_id=f"S{slot_index:02d}_" + "Y" * 119,
                start_ms=slot_index * 10,
                end_ms=slot_index * 10 + 9,
                candidates=hypotheses,
                resolved_gloss_id=hypotheses[0].gloss_id,
                provenance=GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
            )
        )

    with pytest.raises(ValidationError, match=str(MAX_GLOSS_LATTICE_BYTES)):
        GlossLattice(
            type="gloss_lattice",
            schema_version=GLOSS_LATTICE_SCHEMA_VERSION,
            session_id=SESSION_ID,
            lattice_seq=8,
            utterance_id="oversized-utterance",
            language="sgsl",
            timebase="session_monotonic_ms",
            started_at_ms=0,
            ended_at_ms=640,
            producer=producer(),
            slots=tuple(oversized_slots),
        )
