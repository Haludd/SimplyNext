"""Acceptance tests for the frozen CTR GlossLattice version 1.0 contract."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from simplynext.contracts import (
    GLOSS_LATTICE_CONFIDENCE_KIND,
    GLOSS_LATTICE_SCHEMA_VERSION,
    GLOSS_LATTICE_TIMEBASE,
    MAX_GLOSS_CANDIDATES_PER_SLOT,
    MAX_GLOSS_LATTICE_BYTES,
    MAX_GLOSS_LATTICE_SLOTS,
    GlossCandidate,
    GlossLattice,
    GlossLatticeProducer,
    GlossProvenance,
    GlossSlot,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gloss_lattice_v1.json"
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
PathPart = str | int


def _fixture_bytes() -> bytes:
    return FIXTURE_PATH.read_bytes()


def _fixture_payload() -> dict[str, Any]:
    decoded = json.loads(_fixture_bytes())
    assert isinstance(decoded, dict)
    return decoded


def _validate(payload: object) -> GlossLattice:
    raw = json.dumps(payload, separators=(",", ":"), allow_nan=True)
    return GlossLattice.model_validate_json(raw)


def _target(payload: object, path: tuple[PathPart, ...]) -> Any:
    target = payload
    for component in path:
        target = target[component]  # type: ignore[index]
    return target


def _set(payload: object, path: tuple[PathPart, ...], value: object) -> None:
    parent = _target(payload, path[:-1])
    parent[path[-1]] = value


def _delete(payload: object, path: tuple[PathPart, ...]) -> None:
    parent = _target(payload, path[:-1])
    del parent[path[-1]]


def _candidate(
    gloss_id: str = "HELLO",
    rank: int = 1,
    confidence: float | int = 0.95,
) -> dict[str, object]:
    return {"gloss_id": gloss_id, "rank": rank, "confidence": confidence}


def _slot(
    slot_index: int,
    start_ms: int,
    end_ms: int,
    *,
    slot_id: str | None = None,
    candidates: list[dict[str, object]] | None = None,
    resolved_gloss_id: str | None = None,
    provenance: str = "unresolved",
) -> dict[str, object]:
    return {
        "slot_index": slot_index,
        "slot_id": slot_id or f"slot-{slot_index}",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "candidates": candidates or [],
        "resolved_gloss_id": resolved_gloss_id,
        "provenance": provenance,
    }


def _payload_with_slots(
    slots: list[dict[str, object]],
    *,
    started_at_ms: int = 0,
    ended_at_ms: int = 10_000,
) -> dict[str, Any]:
    payload = _fixture_payload()
    payload["started_at_ms"] = started_at_ms
    payload["ended_at_ms"] = ended_at_ms
    payload["slots"] = slots
    return payload


def test_checked_in_ctr_fixture_is_the_exact_round_trip_contract() -> None:
    raw = _fixture_bytes()
    payload = _fixture_payload()

    lattice = GlossLattice.model_validate_json(raw)
    compact = lattice.model_dump_json().encode("utf-8")

    assert lattice.model_dump(mode="json") == payload
    assert GlossLattice.model_validate_json(compact) == lattice
    assert len(compact) <= MAX_GLOSS_LATTICE_BYTES
    assert isinstance(lattice.producer, GlossLatticeProducer)
    assert all(isinstance(slot, GlossSlot) for slot in lattice.slots)
    assert [slot.provenance for slot in lattice.slots] == list(GlossProvenance)


def test_ctr_constants_are_frozen() -> None:
    assert GLOSS_LATTICE_SCHEMA_VERSION == "1.0"
    assert GLOSS_LATTICE_TIMEBASE == "session_monotonic_ms"
    assert GLOSS_LATTICE_CONFIDENCE_KIND == "calibrated_probability"
    assert MAX_GLOSS_LATTICE_BYTES == 32_768
    assert MAX_GLOSS_LATTICE_SLOTS == 64
    assert MAX_GLOSS_CANDIDATES_PER_SLOT == 5


def test_wire_field_sets_match_ctr_at_every_object_level() -> None:
    lattice = GlossLattice.model_validate_json(_fixture_bytes())

    assert set(lattice.model_dump()) == {
        "type",
        "schema_version",
        "session_id",
        "lattice_seq",
        "utterance_id",
        "language",
        "timebase",
        "started_at_ms",
        "ended_at_ms",
        "producer",
        "slots",
    }
    assert set(lattice.producer.model_dump()) == {
        "classifier_id",
        "classifier_version",
        "confidence_kind",
        "calibration_version",
        "vocabulary_version",
    }
    assert set(lattice.slots[0].model_dump()) == {
        "slot_index",
        "slot_id",
        "start_ms",
        "end_ms",
        "candidates",
        "resolved_gloss_id",
        "provenance",
    }
    assert set(lattice.slots[0].candidates[0].model_dump()) == {
        "gloss_id",
        "rank",
        "confidence",
    }


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(("type",), id="envelope-type"),
        pytest.param(("schema_version",), id="envelope-schema-version"),
        pytest.param(("session_id",), id="envelope-session-id"),
        pytest.param(("lattice_seq",), id="envelope-lattice-seq"),
        pytest.param(("utterance_id",), id="envelope-utterance-id"),
        pytest.param(("language",), id="envelope-language"),
        pytest.param(("timebase",), id="envelope-timebase"),
        pytest.param(("started_at_ms",), id="envelope-started-at"),
        pytest.param(("ended_at_ms",), id="envelope-ended-at"),
        pytest.param(("producer",), id="envelope-producer"),
        pytest.param(("slots",), id="envelope-slots"),
        pytest.param(("producer", "classifier_id"), id="producer-classifier-id"),
        pytest.param(("producer", "classifier_version"), id="producer-classifier-version"),
        pytest.param(("producer", "confidence_kind"), id="producer-confidence-kind"),
        pytest.param(("producer", "calibration_version"), id="producer-calibration-version"),
        pytest.param(("producer", "vocabulary_version"), id="producer-vocabulary-version"),
        pytest.param(("slots", 0, "slot_index"), id="slot-index"),
        pytest.param(("slots", 0, "slot_id"), id="slot-id"),
        pytest.param(("slots", 0, "start_ms"), id="slot-start"),
        pytest.param(("slots", 0, "end_ms"), id="slot-end"),
        pytest.param(("slots", 0, "candidates"), id="slot-candidates"),
        pytest.param(("slots", 0, "resolved_gloss_id"), id="slot-resolution"),
        pytest.param(("slots", 0, "provenance"), id="slot-provenance"),
        pytest.param(("slots", 0, "candidates", 0, "gloss_id"), id="candidate-gloss-id"),
        pytest.param(("slots", 0, "candidates", 0, "rank"), id="candidate-rank"),
        pytest.param(("slots", 0, "candidates", 0, "confidence"), id="candidate-confidence"),
    ],
)
def test_every_ctr_field_is_required(path: tuple[PathPart, ...]) -> None:
    payload = _fixture_payload()
    _delete(payload, path)

    with pytest.raises(ValidationError):
        _validate(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param(("type",), "lattice", id="type"),
        pytest.param(("schema_version",), "1.1", id="schema-version"),
        pytest.param(("language",), "bsl", id="language"),
        pytest.param(("timebase",), "unix_ms", id="timebase"),
        pytest.param(
            ("producer", "confidence_kind"),
            "softmax",
            id="confidence-kind",
        ),
    ],
)
def test_fixed_literals_and_enums_reject_other_values(
    path: tuple[PathPart, ...],
    value: object,
) -> None:
    payload = _fixture_payload()
    _set(payload, path, value)

    with pytest.raises(ValidationError):
        _validate(payload)


@pytest.mark.parametrize(
    ("path", "key", "value"),
    [
        pytest.param((), "debug", True, id="envelope"),
        pytest.param(("producer",), "artifact_url", "https://example.invalid", id="producer"),
        pytest.param(("slots", 0), "landmarks", [[0, 0, 0]], id="slot"),
        pytest.param(("slots", 0, "candidates", 0), "logit", 4.2, id="candidate"),
    ],
)
def test_unknown_fields_are_rejected_at_every_object_level(
    path: tuple[PathPart, ...],
    key: str,
    value: object,
) -> None:
    payload = _fixture_payload()
    target = _target(payload, path)
    target[key] = value

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        _validate(payload)


@pytest.mark.parametrize(
    ("path", "key", "value"),
    [
        pytest.param((), "revision", 0, id="revision"),
        pytest.param((), "subject_id", "signer-a", id="subject-id"),
        pytest.param((), "is_final", True, id="is-final"),
        pytest.param((), "capture_start_ms", 1_000, id="capture-start"),
        pytest.param((), "capture_end_ms", 3_000, id="capture-end"),
        pytest.param((), "produced_ms", 3_100, id="produced"),
        pytest.param((), "quality", {}, id="quality"),
        pytest.param(("producer",), "classifier", {}, id="nested-classifier"),
        pytest.param(("producer",), "segmenter_version", "v1", id="segmenter-version"),
        pytest.param(("producer",), "top_k", 5, id="top-k"),
        pytest.param(("slots", 0), "resolved_gloss", "WATER", id="resolved-gloss"),
        pytest.param(("slots", 0), "selected_rank", 1, id="selected-rank"),
        pytest.param(("slots", 0), "confirmed_at_ms", 1_200, id="confirmed-at"),
        pytest.param(("slots", 0), "reason_codes", [], id="reason-codes"),
        pytest.param(("slots", 0, "candidates", 0), "gloss", "WATER", id="gloss"),
    ],
)
def test_legacy_contract_fields_are_not_accepted_as_aliases(
    path: tuple[PathPart, ...],
    key: str,
    value: object,
) -> None:
    payload = _fixture_payload()
    target = _target(payload, path)
    target[key] = value

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        _validate(payload)


STRICT_NUMERIC_CASES = [
    pytest.param(("lattice_seq",), "7", id="lattice-seq-string"),
    pytest.param(("lattice_seq",), True, id="lattice-seq-boolean"),
    pytest.param(("lattice_seq",), 7.0, id="lattice-seq-float"),
    pytest.param(("started_at_ms",), "1000", id="started-at-string"),
    pytest.param(("started_at_ms",), False, id="started-at-boolean"),
    pytest.param(("ended_at_ms",), "3000", id="ended-at-string"),
    pytest.param(("ended_at_ms",), True, id="ended-at-boolean"),
    pytest.param(("slots", 0, "slot_index"), "0", id="slot-index-string"),
    pytest.param(("slots", 0, "slot_index"), False, id="slot-index-boolean"),
    pytest.param(("slots", 0, "start_ms"), "1000", id="slot-start-string"),
    pytest.param(("slots", 0, "start_ms"), True, id="slot-start-boolean"),
    pytest.param(("slots", 0, "end_ms"), "1300", id="slot-end-string"),
    pytest.param(("slots", 0, "end_ms"), True, id="slot-end-boolean"),
    pytest.param(("slots", 0, "candidates", 0, "rank"), "1", id="rank-string"),
    pytest.param(("slots", 0, "candidates", 0, "rank"), True, id="rank-boolean"),
    pytest.param(
        ("slots", 0, "candidates", 0, "confidence"),
        "0.96",
        id="confidence-string",
    ),
    pytest.param(
        ("slots", 0, "candidates", 0, "confidence"),
        True,
        id="confidence-boolean",
    ),
]


@pytest.mark.parametrize(("path", "value"), STRICT_NUMERIC_CASES)
def test_numeric_strings_booleans_and_integral_floats_are_not_coerced(
    path: tuple[PathPart, ...],
    value: object,
) -> None:
    payload = _fixture_payload()
    _set(payload, path, value)

    with pytest.raises(ValidationError):
        _validate(payload)


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), -float("inf"), -0.01, 1.01])
def test_confidence_must_be_finite_and_between_zero_and_one(confidence: float) -> None:
    payload = _fixture_payload()
    payload["slots"][0]["candidates"][0]["confidence"] = confidence

    with pytest.raises(ValidationError):
        _validate(payload)


@pytest.mark.parametrize("confidence", [0, 1])
def test_integer_confidence_endpoints_are_valid_json_numbers(confidence: int) -> None:
    candidate = GlossCandidate.model_validate_json(
        json.dumps({"gloss_id": "ENDPOINT", "rank": 1, "confidence": confidence})
    )

    assert candidate.confidence == float(confidence)


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(("session_id",), id="session-id"),
        pytest.param(("utterance_id",), id="utterance-id"),
        pytest.param(("producer", "classifier_id"), id="classifier-id"),
        pytest.param(("producer", "classifier_version"), id="classifier-version"),
        pytest.param(("producer", "calibration_version"), id="calibration-version"),
        pytest.param(("producer", "vocabulary_version"), id="vocabulary-version"),
        pytest.param(("slots", 0, "slot_id"), id="slot-id"),
        pytest.param(("slots", 0, "resolved_gloss_id"), id="resolved-gloss-id"),
        pytest.param(("slots", 0, "candidates", 0, "gloss_id"), id="candidate-gloss-id"),
    ],
)
def test_surrounding_identifier_whitespace_is_rejected(path: tuple[PathPart, ...]) -> None:
    payload = _fixture_payload()
    original = _target(payload, path)
    _set(payload, path, f" {original} ")

    with pytest.raises(ValidationError):
        _validate(payload)


@pytest.mark.parametrize("value", ["HAS SPACE", "slash/value", "é", "_leading", ""])
def test_gloss_ids_use_the_frozen_identifier_syntax(value: str) -> None:
    with pytest.raises(ValidationError):
        GlossCandidate.model_validate({"gloss_id": value, "rank": 1, "confidence": 0.5})


def test_identifier_length_boundary_is_enforced() -> None:
    accepted = GlossCandidate.model_validate({"gloss_id": "X" * 128, "rank": 1, "confidence": 0.5})
    assert len(accepted.gloss_id) == 128

    with pytest.raises(ValidationError):
        GlossCandidate.model_validate({"gloss_id": "X" * 129, "rank": 1, "confidence": 0.5})


def test_models_are_immutable_at_every_nested_level() -> None:
    lattice = GlossLattice.model_validate_json(_fixture_bytes())

    for model, field, value in (
        (lattice, "lattice_seq", 8),
        (lattice.producer, "classifier_version", "2.0.0"),
        (lattice.slots[0], "slot_id", "changed"),
        (lattice.slots[0].candidates[0], "gloss_id", "CHANGED"),
    ):
        with pytest.raises(ValidationError, match="frozen"):
            setattr(model, field, value)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param(("lattice_seq",), -1, id="lattice-seq-negative"),
        pytest.param(("lattice_seq",), MAX_SAFE_JSON_INTEGER + 1, id="lattice-seq-too-large"),
        pytest.param(("started_at_ms",), -1, id="started-at-negative"),
        pytest.param(("started_at_ms",), MAX_SAFE_JSON_INTEGER + 1, id="started-at-too-large"),
        pytest.param(("ended_at_ms",), -1, id="ended-at-negative"),
        pytest.param(("ended_at_ms",), MAX_SAFE_JSON_INTEGER + 1, id="ended-at-too-large"),
        pytest.param(("slots", 0, "slot_index"), -1, id="slot-index-negative"),
        pytest.param(("slots", 0, "slot_index"), 64, id="slot-index-too-large"),
        pytest.param(("slots", 0, "start_ms"), -1, id="slot-start-negative"),
        pytest.param(
            ("slots", 0, "start_ms"),
            MAX_SAFE_JSON_INTEGER + 1,
            id="slot-start-too-large",
        ),
        pytest.param(("slots", 0, "end_ms"), -1, id="slot-end-negative"),
        pytest.param(("slots", 0, "end_ms"), MAX_SAFE_JSON_INTEGER + 1, id="slot-end-too-large"),
        pytest.param(("slots", 0, "candidates", 0, "rank"), 0, id="rank-zero"),
        pytest.param(("slots", 0, "candidates", 0, "rank"), 6, id="rank-six"),
    ],
)
def test_numeric_bounds_are_enforced(path: tuple[PathPart, ...], value: int) -> None:
    payload = _fixture_payload()
    _set(payload, path, value)

    with pytest.raises(ValidationError):
        _validate(payload)


def test_safe_json_integer_and_half_open_end_boundaries_are_valid() -> None:
    slot = _slot(
        0,
        MAX_SAFE_JSON_INTEGER - 10,
        MAX_SAFE_JSON_INTEGER,
        candidates=[_candidate("LIMIT", 1, 1)],
        resolved_gloss_id="LIMIT",
        provenance="classifier_high_confidence",
    )
    payload = _payload_with_slots(
        [slot],
        started_at_ms=MAX_SAFE_JSON_INTEGER - 10,
        ended_at_ms=MAX_SAFE_JSON_INTEGER,
    )
    payload["lattice_seq"] = MAX_SAFE_JSON_INTEGER

    lattice = _validate(payload)

    assert lattice.slots[0].end_ms == lattice.ended_at_ms


@pytest.mark.parametrize(
    ("started_at_ms", "ended_at_ms"),
    [(1_000, 1_000), (1_001, 1_000)],
)
def test_utterance_interval_must_have_positive_duration(
    started_at_ms: int,
    ended_at_ms: int,
) -> None:
    payload = _fixture_payload()
    payload["started_at_ms"] = started_at_ms
    payload["ended_at_ms"] = ended_at_ms

    with pytest.raises(ValidationError, match="ended_at_ms must be greater"):
        _validate(payload)


def test_slot_interval_must_have_positive_duration() -> None:
    payload = _fixture_payload()
    payload["slots"][0]["end_ms"] = payload["slots"][0]["start_ms"]

    with pytest.raises(ValidationError, match="end_ms must be greater"):
        _validate(payload)


@pytest.mark.parametrize(
    ("start_ms", "end_ms"),
    [(999, 1_100), (2_900, 3_001)],
)
def test_every_slot_must_lie_inside_the_utterance_interval(
    start_ms: int,
    end_ms: int,
) -> None:
    payload = _fixture_payload()
    payload["slots"] = [_slot(0, start_ms, end_ms)]

    with pytest.raises(ValidationError, match="inside the utterance interval"):
        _validate(payload)


def test_zero_and_sixty_five_slots_are_rejected() -> None:
    empty = _payload_with_slots([])
    too_many = _payload_with_slots(
        [_slot(index, index * 2, index * 2 + 1) for index in range(65)],
        ended_at_ms=130,
    )

    with pytest.raises(ValidationError):
        _validate(empty)
    with pytest.raises(ValidationError):
        _validate(too_many)


def test_sixty_four_minimal_slots_are_valid() -> None:
    payload = _payload_with_slots(
        [_slot(index, index * 2, index * 2 + 1) for index in range(64)],
        ended_at_ms=128,
    )

    lattice = _validate(payload)

    assert len(lattice.slots) == 64
    assert lattice.slots[-1].slot_index == 63


@pytest.mark.parametrize(
    "indices",
    [
        pytest.param([1], id="does-not-start-at-zero"),
        pytest.param([0, 2], id="gap"),
        pytest.param([1, 0], id="does-not-match-array-order"),
    ],
)
def test_slot_indices_are_contiguous_and_match_array_order(indices: list[int]) -> None:
    slots = [
        _slot(index, position * 20, position * 20 + 10) for position, index in enumerate(indices)
    ]

    with pytest.raises(ValidationError, match="slot_index values must be contiguous"):
        _validate(_payload_with_slots(slots))


def test_slot_ids_must_be_unique_within_the_lattice() -> None:
    slots = [
        _slot(0, 0, 10, slot_id="same"),
        _slot(1, 20, 30, slot_id="same"),
    ]

    with pytest.raises(ValidationError, match="slot_id values must be unique"):
        _validate(_payload_with_slots(slots))


def test_overlapping_slots_are_rejected() -> None:
    slots = [_slot(0, 0, 20), _slot(1, 19, 30)]

    with pytest.raises(ValidationError, match="slot intervals must not overlap"):
        _validate(_payload_with_slots(slots))


@pytest.mark.parametrize("second_start", [20, 25], ids=["adjacent", "gap"])
def test_adjacent_and_gapped_slots_are_valid(second_start: int) -> None:
    slots = [_slot(0, 0, 20), _slot(1, second_start, 40)]

    lattice = _validate(_payload_with_slots(slots))

    assert len(lattice.slots) == 2


@pytest.mark.parametrize(
    "candidates",
    [
        pytest.param([_candidate("A", 2, 0.9)], id="rank-does-not-start-at-one"),
        pytest.param(
            [_candidate("A", 1, 0.9), _candidate("B", 3, 0.8)],
            id="rank-gap",
        ),
        pytest.param(
            [_candidate("A", 1, 0.7), _candidate("B", 2, 0.8)],
            id="confidence-increases",
        ),
    ],
)
def test_candidate_rank_and_confidence_order_is_enforced(
    candidates: list[dict[str, object]],
) -> None:
    slot = _slot(
        0,
        0,
        10,
        candidates=candidates,
        resolved_gloss_id="A",
        provenance="classifier_high_confidence",
    )

    with pytest.raises(ValidationError):
        _validate(_payload_with_slots([slot]))


def test_equal_candidate_confidences_and_incomplete_probability_mass_are_valid() -> None:
    candidates = [_candidate("A", 1, 0.4), _candidate("B", 2, 0.4)]
    slot = _slot(
        0,
        0,
        10,
        candidates=candidates,
        resolved_gloss_id="A",
        provenance="classifier_high_confidence",
    )

    lattice = _validate(_payload_with_slots([slot]))

    assert sum(item.confidence for item in lattice.slots[0].candidates) == pytest.approx(0.8)


def test_more_than_five_candidates_are_rejected() -> None:
    candidates = [_candidate(f"GLOSS_{rank}", rank, 1 - rank / 10) for rank in range(1, 7)]
    slot = _slot(0, 0, 10, candidates=candidates, resolved_gloss_id=None)

    with pytest.raises(ValidationError):
        _validate(_payload_with_slots([slot]))


def test_candidate_gloss_ids_are_unique_but_case_sensitive() -> None:
    exact_duplicates = [_candidate("WATER", 1, 0.9), _candidate("WATER", 2, 0.8)]
    case_distinct = [_candidate("WATER", 1, 0.9), _candidate("water", 2, 0.8)]

    with pytest.raises(ValidationError, match="gloss_id values must be unique"):
        _validate(
            _payload_with_slots(
                [
                    _slot(
                        0,
                        0,
                        10,
                        candidates=exact_duplicates,
                        resolved_gloss_id="WATER",
                        provenance="classifier_high_confidence",
                    )
                ]
            )
        )

    lattice = _validate(
        _payload_with_slots(
            [
                _slot(
                    0,
                    0,
                    10,
                    candidates=case_distinct,
                    resolved_gloss_id="WATER",
                    provenance="classifier_high_confidence",
                )
            ]
        )
    )
    assert [item.gloss_id for item in lattice.slots[0].candidates] == ["WATER", "water"]


VALID_PROVENANCE_SLOTS = [
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("WATER", 1, 0.96), _candidate("WHAT", 2, 0.02)],
            resolved_gloss_id="WATER",
            provenance="classifier_high_confidence",
        ),
        "WATER",
        id="classifier-high-confidence",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("PLEASE", 1, 0.57), _candidate("THANK_YOU", 2, 0.31)],
            resolved_gloss_id="THANK_YOU",
            provenance="top_k_signer_confirmed",
        ),
        "THANK_YOU",
        id="top-k-signer-confirmed",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[],
            resolved_gloss_id="J-O-H-N",
            provenance="fingerspelled",
        ),
        "J-O-H-N",
        id="fingerspelled-empty-candidates",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("JOHN", 1, 0.3)],
            resolved_gloss_id="J-O-H-N",
            provenance="fingerspelled",
        ),
        "J-O-H-N",
        id="fingerspelled-resolution-not-retained",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("TOMORROW", 1, 0.42)],
            resolved_gloss_id=None,
            provenance="unresolved",
        ),
        None,
        id="unresolved-retained-candidates",
    ),
    pytest.param(_slot(0, 0, 10), None, id="unresolved-empty-candidates"),
]


@pytest.mark.parametrize(("slot", "expected_resolution"), VALID_PROVENANCE_SLOTS)
def test_all_ctr_provenance_states_accept_their_valid_shapes(
    slot: dict[str, object],
    expected_resolution: str | None,
) -> None:
    lattice = _validate(_payload_with_slots([deepcopy(slot)]))

    assert lattice.slots[0].resolved_gloss_id == expected_resolution


INVALID_PROVENANCE_SLOTS = [
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[],
            resolved_gloss_id="WATER",
            provenance="classifier_high_confidence",
        ),
        id="classifier-no-candidates",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("WATER")],
            resolved_gloss_id=None,
            provenance="classifier_high_confidence",
        ),
        id="classifier-null-resolution",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("WATER", 1, 0.9), _candidate("WHAT", 2, 0.8)],
            resolved_gloss_id="WHAT",
            provenance="classifier_high_confidence",
        ),
        id="classifier-not-rank-one",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[],
            resolved_gloss_id="WATER",
            provenance="top_k_signer_confirmed",
        ),
        id="confirmed-no-candidates",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("WATER")],
            resolved_gloss_id=None,
            provenance="top_k_signer_confirmed",
        ),
        id="confirmed-null-resolution",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            candidates=[_candidate("WATER")],
            resolved_gloss_id="WHAT",
            provenance="top_k_signer_confirmed",
        ),
        id="confirmed-resolution-not-retained",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            resolved_gloss_id=None,
            provenance="fingerspelled",
        ),
        id="fingerspelled-null-resolution",
    ),
    pytest.param(
        _slot(
            0,
            0,
            10,
            resolved_gloss_id="WATER",
            provenance="unresolved",
        ),
        id="unresolved-has-resolution",
    ),
]


@pytest.mark.parametrize("slot", INVALID_PROVENANCE_SLOTS)
def test_invalid_provenance_resolution_combinations_are_rejected(
    slot: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _validate(_payload_with_slots([deepcopy(slot)]))


def test_resolution_matching_is_exact_and_case_sensitive() -> None:
    slot = _slot(
        0,
        0,
        10,
        candidates=[_candidate("WATER")],
        resolved_gloss_id="water",
        provenance="classifier_high_confidence",
    )

    with pytest.raises(ValidationError):
        _validate(_payload_with_slots([slot]))


@pytest.mark.parametrize("raw", [b"[]", b"null", b"{}{}"])
def test_json_input_must_contain_exactly_one_object(raw: bytes) -> None:
    with pytest.raises(ValidationError):
        GlossLattice.model_validate_json(raw)


def test_generated_json_schema_exposes_the_frozen_shape() -> None:
    schema = GlossLattice.model_json_schema()
    producer = schema["$defs"]["GlossLatticeProducer"]
    slot = schema["$defs"]["GlossSlot"]
    candidate = schema["$defs"]["GlossCandidate"]

    assert schema["additionalProperties"] is False
    assert producer["additionalProperties"] is False
    assert slot["additionalProperties"] is False
    assert candidate["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert set(producer["required"]) == set(producer["properties"])
    assert set(slot["required"]) == set(slot["properties"])
    assert set(candidate["required"]) == set(candidate["properties"])
    assert schema["properties"]["type"]["const"] == "gloss_lattice"
    assert schema["properties"]["schema_version"]["const"] == "1.0"
    assert schema["properties"]["timebase"]["const"] == "session_monotonic_ms"
    assert schema["properties"]["slots"]["minItems"] == 1
    assert schema["properties"]["slots"]["maxItems"] == 64
    assert slot["properties"]["candidates"]["maxItems"] == 5
