from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from simplynext.contracts import (
    MAX_GLOSS_CANDIDATES_PER_SLOT,
    MAX_GLOSS_LATTICE_BYTES,
    MAX_GLOSS_LATTICE_SLOTS,
    ClassifierDescriptor,
    GlossLattice,
    GlossLatticeProducer,
    GlossLatticeSlot,
    GlossProvenance,
)

SESSION_ID = "3dd5e15d-991a-4c27-9a11-af4a1a3bb2e8"


def _candidate(
    rank: int = 1,
    gloss: str = "HELLO",
    confidence: float = 0.94,
) -> dict[str, object]:
    return {"rank": rank, "gloss": gloss, "confidence": confidence}


def _slot_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "slot_id": "s0",
        "start_ms": 1_100,
        "end_ms": 1_700,
        "candidates": [_candidate()],
        "resolved_gloss": "HELLO",
        "selected_rank": 1,
        "provenance": "classifier_high_confidence",
        "confirmed_at_ms": None,
        "reason_codes": [],
    }
    payload.update(overrides)
    return payload


def _producer_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "classifier": {
            "name": "simplynext-temporal",
            "model_version": "sgsl-v3",
            "calibration_version": "temperature-v2",
            "vocabulary_version": "informal-v1",
        },
        "segmenter_version": "geometry-v2",
        "top_k": 5,
    }
    payload.update(overrides)
    return payload


def _lattice_payload(
    *,
    slots: list[dict[str, object]] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "gloss_lattice",
        "schema_version": "1.0",
        "session_id": SESSION_ID,
        "lattice_seq": 7,
        "utterance_id": "utt-019",
        "revision": 0,
        "language": "sgsl",
        "subject_id": "track-4",
        "is_final": True,
        "capture_start_ms": 1_000,
        "capture_end_ms": 5_000,
        "produced_ms": 5_200,
        "producer": _producer_payload(),
        "quality": {
            "observed_frames": 46,
            "dropped_frames": 1,
            "landmark_coverage": 0.94,
            "classifier_latency_ms": 31,
        },
        "slots": slots if slots is not None else [_slot_payload()],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("slot", "expected_gloss"),
    [
        pytest.param(_slot_payload(), "HELLO", id="classifier-high-confidence"),
        pytest.param(
            _slot_payload(
                candidates=[
                    _candidate(1, "WATER", 0.54),
                    _candidate(2, "DRINK", 0.49),
                ],
                resolved_gloss="DRINK",
                selected_rank=2,
                provenance="top_k_signer_confirmed",
                confirmed_at_ms=5_100,
            ),
            "DRINK",
            id="top-k-signer-confirmed",
        ),
        pytest.param(
            _slot_payload(
                candidates=[],
                resolved_gloss="WILLIAM",
                selected_rank=None,
                provenance="fingerspelled",
                confirmed_at_ms=5_100,
            ),
            "WILLIAM",
            id="fingerspelled",
        ),
        pytest.param(
            _slot_payload(
                candidates=[_candidate(1, "WATER", 0.54)],
                resolved_gloss=None,
                selected_rank=None,
                provenance="unresolved",
                reason_codes=["below_threshold"],
            ),
            None,
            id="unresolved",
        ),
    ],
)
def test_each_provenance_rung_has_a_valid_fixture(
    slot: dict[str, object],
    expected_gloss: str | None,
) -> None:
    lattice = GlossLattice.model_validate(_lattice_payload(slots=[slot]))

    assert lattice.slots[0].resolved_gloss == expected_gloss
    assert lattice.slots[0].provenance in GlossProvenance


def test_multi_slot_lattice_round_trips_through_compact_json() -> None:
    slots = [
        _slot_payload(slot_id="s0", start_ms=1_100, end_ms=1_700),
        _slot_payload(
            slot_id="s1",
            start_ms=1_800,
            end_ms=2_500,
            candidates=[
                _candidate(1, "WATER", 0.54),
                _candidate(2, "DRINK", 0.49),
            ],
            resolved_gloss="DRINK",
            selected_rank=2,
            provenance="top_k_signer_confirmed",
            confirmed_at_ms=5_100,
        ),
        _slot_payload(
            slot_id="s2",
            start_ms=2_600,
            end_ms=3_200,
            candidates=[],
            resolved_gloss="WILLIAM",
            selected_rank=None,
            provenance="fingerspelled",
            confirmed_at_ms=5_100,
        ),
        _slot_payload(
            slot_id="s3",
            start_ms=3_300,
            end_ms=4_600,
            candidates=[_candidate(1, "PLEASE", 0.47)],
            resolved_gloss=None,
            selected_rank=None,
            provenance="unresolved",
            reason_codes=["ambiguous_top_k"],
        ),
    ]
    lattice = GlossLattice.model_validate(_lattice_payload(slots=slots))

    encoded = lattice.model_dump_json().encode("utf-8")

    assert len(encoded) <= MAX_GLOSS_LATTICE_BYTES
    assert GlossLattice.model_validate_json(encoded) == lattice
    assert [slot.slot_id for slot in lattice.slots] == ["s0", "s1", "s2", "s3"]


def test_maximum_shape_lattice_stays_below_the_serialized_size_ceiling() -> None:
    maximum_safe_integer = 9_007_199_254_740_991
    capture_start_ms = maximum_safe_integer - 5_000
    slots: list[dict[str, object]] = []
    for slot_index in range(MAX_GLOSS_LATTICE_SLOTS):
        candidates = []
        for rank in range(1, MAX_GLOSS_CANDIDATES_PER_SLOT + 1):
            prefix = f"S{slot_index:02d}_R{rank}_"
            candidates.append(
                _candidate(
                    rank,
                    prefix + "X" * (128 - len(prefix)),
                    1.0 - rank / 10,
                )
            )
        slots.append(
            _slot_payload(
                slot_id=(f"s{slot_index}_" + "S" * 128)[:128],
                start_ms=capture_start_ms + slot_index * 100,
                end_ms=capture_start_ms + 50 + slot_index * 100,
                candidates=candidates,
                resolved_gloss=candidates[0]["gloss"],
                reason_codes=[
                    (f"r{slot_index}_{reason_index}_" + "x" * 64)[:64] for reason_index in range(8)
                ],
            )
        )
    payload = _lattice_payload(
        slots=slots,
        lattice_seq=maximum_safe_integer,
        utterance_id="U" * 128,
        subject_id="S" * 128,
        capture_start_ms=capture_start_ms,
        capture_end_ms=capture_start_ms + 4_200,
        produced_ms=capture_start_ms + 4_300,
        quality={
            "observed_frames": 100_000,
            "dropped_frames": 100_000,
            "landmark_coverage": 1.0,
            "classifier_latency_ms": 60_000,
        },
    )
    payload["producer"] = {
        "classifier": {
            "name": "N" * 128,
            "model_version": "M" * 128,
            "calibration_version": "C" * 128,
            "vocabulary_version": "V" * 128,
        },
        "segmenter_version": "G" * 128,
        "top_k": MAX_GLOSS_CANDIDATES_PER_SLOT,
    }
    lattice = GlossLattice.model_validate(payload)

    assert len(lattice.model_dump_json().encode("utf-8")) <= MAX_GLOSS_LATTICE_BYTES


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lattice_seq", 9_007_199_254_740_992),
        ("capture_start_ms", 9_007_199_254_740_992),
        ("capture_end_ms", 9_007_199_254_740_992),
        ("produced_ms", 9_007_199_254_740_992),
    ],
)
def test_lattice_integers_must_be_json_interoperable(field: str, value: int) -> None:
    with pytest.raises(ValidationError, match="less than or equal"):
        GlossLattice.model_validate(_lattice_payload(**{field: value}))


@pytest.mark.parametrize(
    ("path", "key", "value"),
    [
        pytest.param((), "landmarks", [[0.1, 0.2, 0.3]], id="top-level-landmarks"),
        pytest.param(("slots", 0), "image", "data:image/png;base64,...", id="slot-image"),
        pytest.param(
            ("slots", 0, "candidates", 0),
            "coordinates",
            [0.1, 0.2],
            id="candidate-coordinates",
        ),
    ],
)
def test_raw_media_and_unknown_fields_are_rejected(
    path: tuple[str | int, ...],
    key: str,
    value: object,
) -> None:
    payload = deepcopy(_lattice_payload())
    target: Any = payload
    for component in path:
        target = target[component]
    target[key] = value

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        GlossLattice.model_validate(payload)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        pytest.param(
            {"candidates": [_candidate(2)]},
            "candidate ranks must be contiguous",
            id="rank-does-not-start-at-one",
        ),
        pytest.param(
            {
                "candidates": [
                    _candidate(1, "HELLO", 0.9),
                    _candidate(3, "WELCOME", 0.8),
                ]
            },
            "candidate ranks must be contiguous",
            id="rank-gap",
        ),
        pytest.param(
            {
                "candidates": [
                    _candidate(1, "HELLO", 0.7),
                    _candidate(2, "WELCOME", 0.8),
                ]
            },
            "non-increasing confidence",
            id="confidence-order",
        ),
        pytest.param(
            {
                "candidates": [
                    _candidate(1, "GOOD MORNING", 0.9),
                    _candidate(2, "good_morning", 0.8),
                ]
            },
            "candidate glosses must be unique",
            id="canonical-gloss-duplicate",
        ),
        pytest.param(
            {"reason_codes": ["low_confidence", "low_confidence"]},
            "reason_codes must be unique",
            id="reason-code-duplicate",
        ),
    ],
)
def test_candidate_ranks_order_and_duplicates_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        GlossLatticeSlot.model_validate(_slot_payload(**changes))


def test_duplicate_slot_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="slot_id values must be unique"):
        GlossLattice.model_validate(
            _lattice_payload(
                slots=[
                    _slot_payload(slot_id="same", start_ms=1_100, end_ms=1_700),
                    _slot_payload(slot_id="same", start_ms=1_800, end_ms=2_400),
                ]
            )
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        pytest.param(
            _lattice_payload(capture_start_ms=5_000, capture_end_ms=5_000),
            "capture_end_ms must be greater",
            id="empty-capture-interval",
        ),
        pytest.param(
            _lattice_payload(capture_end_ms=5_000, produced_ms=4_999),
            "produced_ms must not precede",
            id="produced-before-capture-end",
        ),
        pytest.param(
            _lattice_payload(slots=[_slot_payload(start_ms=999)]),
            "slot timestamps must lie inside",
            id="slot-before-capture",
        ),
        pytest.param(
            _lattice_payload(slots=[_slot_payload(end_ms=5_001)]),
            "slot timestamps must lie inside",
            id="slot-after-capture",
        ),
        pytest.param(
            _lattice_payload(
                slots=[
                    _slot_payload(slot_id="later", start_ms=2_000, end_ms=2_500),
                    _slot_payload(slot_id="earlier", start_ms=1_500, end_ms=1_900),
                ]
            ),
            "slots must be ordered",
            id="slots-out-of-order",
        ),
        pytest.param(
            _lattice_payload(
                slots=[
                    _slot_payload(
                        provenance="top_k_signer_confirmed",
                        confirmed_at_ms=999,
                    )
                ]
            ),
            "confirmed_at_ms must lie between",
            id="confirmation-before-capture",
        ),
        pytest.param(
            _lattice_payload(
                slots=[
                    _slot_payload(
                        provenance="top_k_signer_confirmed",
                        confirmed_at_ms=5_201,
                    )
                ]
            ),
            "confirmed_at_ms must lie between",
            id="confirmation-after-production",
        ),
    ],
)
def test_lattice_timestamp_bounds_are_enforced(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        GlossLattice.model_validate(payload)


def test_slot_interval_must_have_positive_duration() -> None:
    with pytest.raises(ValidationError, match="end_ms must be greater"):
        GlossLatticeSlot.model_validate(_slot_payload(start_ms=1_100, end_ms=1_100))


@pytest.mark.parametrize("top_k", [0, MAX_GLOSS_CANDIDATES_PER_SLOT + 1])
def test_producer_top_k_is_bounded(top_k: int) -> None:
    with pytest.raises(ValidationError):
        GlossLatticeProducer.model_validate(_producer_payload(top_k=top_k))


def test_slot_candidate_count_cannot_exceed_declared_top_k() -> None:
    candidates = [_candidate(1, "HELLO", 0.9), _candidate(2, "WELCOME", 0.8)]
    payload = _lattice_payload(slots=[_slot_payload(candidates=candidates)])
    payload["producer"] = _producer_payload(top_k=1)

    with pytest.raises(ValidationError, match="candidate count exceeds producer.top_k"):
        GlossLattice.model_validate(payload)


def test_slot_cannot_carry_more_than_five_candidates() -> None:
    candidates = [
        _candidate(rank, f"GLOSS_{rank}", 1.0 - rank / 10)
        for rank in range(1, MAX_GLOSS_CANDIDATES_PER_SLOT + 2)
    ]

    with pytest.raises(ValidationError):
        GlossLatticeSlot.model_validate(_slot_payload(candidates=candidates))


@pytest.mark.parametrize(
    "field",
    ["name", "model_version", "calibration_version", "vocabulary_version"],
)
def test_classifier_profile_identifiers_are_required_and_bounded(field: str) -> None:
    profile = deepcopy(_producer_payload()["classifier"])
    assert isinstance(profile, dict)
    profile[field] = "x" * 129

    with pytest.raises(ValidationError):
        ClassifierDescriptor.model_validate(profile)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        pytest.param(
            {"selected_rank": None, "resolved_gloss": None},
            "classifier_high_confidence must select rank 1",
            id="classifier-without-selection",
        ),
        pytest.param(
            {
                "candidates": [
                    _candidate(1, "HELLO", 0.9),
                    _candidate(2, "WELCOME", 0.8),
                ],
                "selected_rank": 2,
                "resolved_gloss": "WELCOME",
            },
            "classifier_high_confidence must select rank 1",
            id="classifier-selects-rank-two",
        ),
        pytest.param(
            {"confirmed_at_ms": 1_800},
            "classifier_high_confidence cannot have confirmed_at_ms",
            id="classifier-with-confirmation",
        ),
        pytest.param(
            {"resolved_gloss": "WELCOME"},
            "resolved_gloss must equal",
            id="classifier-resolution-mismatch",
        ),
        pytest.param(
            {
                "provenance": "top_k_signer_confirmed",
                "selected_rank": None,
                "resolved_gloss": None,
                "confirmed_at_ms": 1_800,
            },
            "requires a selected candidate",
            id="confirmed-without-selection",
        ),
        pytest.param(
            {"provenance": "top_k_signer_confirmed"},
            "requires confirmed_at_ms",
            id="confirmed-without-timestamp",
        ),
        pytest.param(
            {
                "provenance": "top_k_signer_confirmed",
                "confirmed_at_ms": 1_800,
                "resolved_gloss": "WELCOME",
            },
            "resolved_gloss must equal",
            id="confirmed-resolution-mismatch",
        ),
        pytest.param(
            {
                "provenance": "fingerspelled",
                "resolved_gloss": None,
                "selected_rank": None,
                "confirmed_at_ms": 1_800,
            },
            "fingerspelled requires resolved_gloss",
            id="fingerspelled-without-gloss",
        ),
        pytest.param(
            {
                "provenance": "fingerspelled",
                "selected_rank": 1,
                "confirmed_at_ms": 1_800,
            },
            "fingerspelled cannot select",
            id="fingerspelled-with-rank",
        ),
        pytest.param(
            {
                "provenance": "fingerspelled",
                "resolved_gloss": "WILLIAM",
                "selected_rank": None,
            },
            "fingerspelled requires confirmed_at_ms",
            id="fingerspelled-without-confirmation",
        ),
        pytest.param(
            {
                "provenance": "unresolved",
                "selected_rank": None,
                "reason_codes": ["below_threshold"],
            },
            "unresolved slots cannot contain a resolution",
            id="unresolved-with-gloss",
        ),
        pytest.param(
            {
                "provenance": "unresolved",
                "resolved_gloss": None,
                "selected_rank": None,
                "confirmed_at_ms": 1_800,
                "reason_codes": ["below_threshold"],
            },
            "unresolved slots cannot have confirmed_at_ms",
            id="unresolved-with-confirmation",
        ),
        pytest.param(
            {
                "provenance": "unresolved",
                "resolved_gloss": None,
                "selected_rank": None,
            },
            "unresolved slots require at least one reason_code",
            id="unresolved-without-reason",
        ),
    ],
)
def test_invalid_provenance_combinations_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        GlossLatticeSlot.model_validate(_slot_payload(**changes))


def test_selected_rank_must_identify_an_existing_candidate() -> None:
    with pytest.raises(ValidationError, match="selected_rank does not identify a candidate"):
        GlossLatticeSlot.model_validate(
            _slot_payload(
                provenance="top_k_signer_confirmed",
                selected_rank=2,
                resolved_gloss="WELCOME",
                confirmed_at_ms=1_800,
            )
        )
