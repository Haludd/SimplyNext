from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from simplynext.contracts import (
    ClassifierDescriptor,
    ClientDescriptor,
    ClientPlatform,
    ControlAction,
    DetectorDescriptor,
    GlossCandidate,
    GlossLattice,
    GlossLatticeProducer,
    GlossLatticeSlot,
    GlossProvenance,
    LatticeEvidenceTrace,
    LatticeRepairRequiredEvent,
    LatticeResultEvent,
    RepairAction,
    SessionCreateRequest,
    SignLanguage,
    StreamControlMessage,
    StreamKind,
)
from simplynext.sessions import (
    EphemeralSessionStore,
    InvalidSessionState,
    LatticeConflict,
    LatticeInProgress,
    LatticeQuotaExceeded,
    LatticeRateLimited,
    LatticeReservationDisposition,
    NonMonotonicSequence,
)

SESSION_ID = UUID("12345678-1234-5678-1234-567812345678")
TOKEN = "lattice-test-token-at-least-thirty-two-characters"
PROFILE = ClassifierDescriptor(
    name="simplynext-temporal",
    model_version="sgsl-v3",
    calibration_version="temperature-v2",
    vocabulary_version="informal-v1",
)


@dataclass
class FakeClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def _session_request(
    *,
    stream_kind: StreamKind = StreamKind.GLOSS_LATTICE,
    classifier: ClassifierDescriptor | None = PROFILE,
) -> SessionCreateRequest:
    return SessionCreateRequest(
        language=SignLanguage.SGSL,
        stream_kind=stream_kind,
        client=ClientDescriptor(platform=ClientPlatform.TEST, app_version="lattice-test"),
        detector=DetectorDescriptor(name="frontend-landmarker", version="1"),
        classifier=classifier,
    )


def _store(
    clock: FakeClock,
    *,
    ttl_seconds: int = 600,
    max_lattices_per_session: int = 100,
    max_lattices_per_minute: int = 30,
    max_lattices_per_minute_global: int = 120,
) -> EphemeralSessionStore:
    return EphemeralSessionStore(
        ttl_seconds=ttl_seconds,
        max_lattices_per_session=max_lattices_per_session,
        max_lattices_per_minute=max_lattices_per_minute,
        max_lattices_per_minute_global=max_lattices_per_minute_global,
        clock=clock,
        token_factory=lambda: TOKEN,
        id_factory=lambda: SESSION_ID,
    )


def _lattice(
    *,
    lattice_seq: int = 0,
    utterance_id: str = "utt-0",
    revision: int = 0,
    classifier: ClassifierDescriptor = PROFILE,
    subject_id: str = "signer-a",
) -> GlossLattice:
    candidates = (
        GlossCandidate(rank=1, gloss="HELLO", confidence=0.95),
        GlossCandidate(rank=2, gloss="WELCOME", confidence=0.03),
    )
    return GlossLattice(
        session_id=SESSION_ID,
        lattice_seq=lattice_seq,
        utterance_id=utterance_id,
        revision=revision,
        language=SignLanguage.SGSL,
        subject_id=subject_id,
        is_final=True,
        capture_start_ms=1_000,
        capture_end_ms=1_200,
        produced_ms=1_250,
        producer=GlossLatticeProducer(
            classifier=classifier,
            segmenter_version="segmenter-v1",
            top_k=2,
        ),
        slots=(
            GlossLatticeSlot(
                slot_id="s0",
                start_ms=1_000,
                end_ms=1_200,
                candidates=candidates,
                resolved_gloss="HELLO",
                selected_rank=1,
                provenance=GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE,
            ),
        ),
    )


def _digest(lattice: GlossLattice) -> bytes:
    return hashlib.sha256(lattice.model_dump_json().encode("utf-8")).digest()


def _trace(lattice: GlossLattice) -> tuple[LatticeEvidenceTrace, ...]:
    slot = lattice.slots[0]
    return (
        LatticeEvidenceTrace(
            slot_id=slot.slot_id,
            start_ms=slot.start_ms,
            end_ms=slot.end_ms,
            resolved_gloss=slot.resolved_gloss,
            confidence=slot.selected_candidate.confidence if slot.selected_candidate else None,
            provenance=slot.provenance,
            candidates=slot.candidates,
        ),
    )


def _repair(lattice: GlossLattice) -> LatticeRepairRequiredEvent:
    return LatticeRepairRequiredEvent(
        lattice_seq=lattice.lattice_seq,
        utterance_id=lattice.utterance_id,
        revision=lattice.revision,
        action=RepairAction.REPEAT,
        message="Please repeat the sign.",
        confidence=0.40,
        target_slot_ids=(lattice.slots[0].slot_id,),
        reason_codes=("critic_rejected_caption",),
        evidence_trace=_trace(lattice),
        classifier_model_version=PROFILE.model_version,
        agent_source="test-agent",
    )


def _confident(lattice: GlossLattice) -> LatticeResultEvent:
    return LatticeResultEvent(
        lattice_seq=lattice.lattice_seq,
        utterance_id=lattice.utterance_id,
        revision=lattice.revision,
        caption="Hello.",
        tts_text="Hello.",
        confidence=0.95,
        gloss_trace=("HELLO",),
        evidence_trace=_trace(lattice),
        classifier_model_version=PROFILE.model_version,
        agent_source="test-agent",
    )


@pytest.mark.asyncio
async def test_lattice_session_negotiates_path_and_profile() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)

    created = await store.create(_session_request())
    snapshot = await store.authenticate(SESSION_ID, TOKEN)

    expected_path = f"/v1/sessions/{SESSION_ID}/lattices"
    assert created.stream_kind is StreamKind.GLOSS_LATTICE
    assert created.websocket_path == expected_path
    assert created.lattice_websocket_path == expected_path
    assert created.lattice_schema_version == "1.0"
    assert snapshot.stream_kind is StreamKind.GLOSS_LATTICE
    assert snapshot.classifier == PROFILE


@pytest.mark.asyncio
async def test_exact_completed_lattice_replays_cached_terminal_event() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock, max_lattices_per_session=1, max_lattices_per_minute=1)
    await store.create(_session_request())
    lattice = _lattice()
    digest = _digest(lattice)

    accepted = await store.reserve_lattice(lattice, TOKEN, digest)
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED
    with pytest.raises(LatticeInProgress):
        await store.reserve_lattice(lattice, TOKEN, digest)

    terminal = _repair(lattice)
    await store.complete_lattice(lattice, TOKEN, digest, terminal)
    cached = await store.reserve_lattice(lattice, TOKEN, digest)

    assert cached.disposition is LatticeReservationDisposition.CACHED
    assert cached.cached_event == terminal
    assert (await store.authenticate(SESSION_ID, TOKEN)).lattice_count == 1


@pytest.mark.asyncio
async def test_same_utterance_revision_with_changed_content_conflicts() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    original = _lattice()
    changed = _lattice(subject_id="signer-b")

    await store.reserve_lattice(original, TOKEN, _digest(original))
    with pytest.raises(LatticeConflict, match="different content"):
        await store.reserve_lattice(changed, TOKEN, _digest(changed))

    snapshot = await store.authenticate(SESSION_ID, TOKEN)
    assert snapshot.last_lattice_seq == 0
    assert snapshot.lattice_count == 1


@pytest.mark.asyncio
async def test_lattice_sequence_is_strictly_monotonic_per_session() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    first = _lattice(lattice_seq=2, utterance_id="utt-2")
    stale = _lattice(lattice_seq=1, utterance_id="utt-1")
    next_lattice = _lattice(lattice_seq=3, utterance_id="utt-3")

    await store.reserve_lattice(first, TOKEN, _digest(first))
    await store.complete_lattice(first, TOKEN, _digest(first), _confident(first))
    with pytest.raises(NonMonotonicSequence):
        await store.reserve_lattice(stale, TOKEN, _digest(stale))
    accepted = await store.reserve_lattice(next_lattice, TOKEN, _digest(next_lattice))

    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED
    snapshot = await store.authenticate(SESSION_ID, TOKEN)
    assert snapshot.last_lattice_seq == 3
    assert snapshot.lattice_count == 2


@pytest.mark.asyncio
async def test_revision_is_allowed_only_after_a_completed_repair() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    original = _lattice()
    revision = _lattice(lattice_seq=1, revision=1)

    await store.reserve_lattice(original, TOKEN, _digest(original))
    with pytest.raises(LatticeInProgress, match="still being processed"):
        await store.reserve_lattice(revision, TOKEN, _digest(revision))

    await store.complete_lattice(original, TOKEN, _digest(original), _repair(original))
    accepted = await store.reserve_lattice(revision, TOKEN, _digest(revision))

    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED
    assert accepted.revision == 1


@pytest.mark.asyncio
async def test_confident_terminal_result_cannot_be_revised() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    original = _lattice()
    revision = _lattice(lattice_seq=1, revision=1)
    digest = _digest(original)

    await store.reserve_lattice(original, TOKEN, digest)
    await store.complete_lattice(original, TOKEN, digest, _confident(original))

    with pytest.raises(LatticeConflict, match="only a repair response"):
        await store.reserve_lattice(revision, TOKEN, _digest(revision))
    assert (await store.authenticate(SESSION_ID, TOKEN)).lattice_count == 1


@pytest.mark.asyncio
async def test_paused_session_rejects_lattice_without_consuming_sequence() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    await store.apply_control(
        StreamControlMessage(
            session_id=SESSION_ID,
            control_seq=0,
            action=ControlAction.START,
        ),
        TOKEN,
    )
    await store.apply_control(
        StreamControlMessage(
            session_id=SESSION_ID,
            control_seq=1,
            action=ControlAction.PAUSE,
        ),
        TOKEN,
    )
    lattice = _lattice()

    with pytest.raises(InvalidSessionState, match="paused"):
        await store.reserve_lattice(lattice, TOKEN, _digest(lattice))
    paused = await store.authenticate(SESSION_ID, TOKEN)
    assert paused.last_lattice_seq is None
    assert paused.lattice_count == 0

    await store.apply_control(
        StreamControlMessage(
            session_id=SESSION_ID,
            control_seq=2,
            action=ControlAction.RESUME,
        ),
        TOKEN,
    )
    accepted = await store.reserve_lattice(lattice, TOKEN, _digest(lattice))
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED


@pytest.mark.asyncio
async def test_per_minute_rate_limit_expires_without_consuming_rejected_lattice() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock, max_lattices_per_session=10, max_lattices_per_minute=2)
    await store.create(_session_request())
    first = _lattice(lattice_seq=0, utterance_id="utt-0")
    second = _lattice(lattice_seq=1, utterance_id="utt-1")
    third = _lattice(lattice_seq=2, utterance_id="utt-2")

    await store.reserve_lattice(first, TOKEN, _digest(first))
    await store.complete_lattice(first, TOKEN, _digest(first), _confident(first))
    await store.reserve_lattice(second, TOKEN, _digest(second))
    await store.complete_lattice(second, TOKEN, _digest(second), _confident(second))
    with pytest.raises(LatticeRateLimited):
        await store.reserve_lattice(third, TOKEN, _digest(third))
    assert (await store.authenticate(SESSION_ID, TOKEN)).lattice_count == 2

    clock.advance(seconds=60)
    accepted = await store.reserve_lattice(third, TOKEN, _digest(third))
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED


@pytest.mark.asyncio
async def test_per_session_lattice_quota_is_permanent_for_session() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock, max_lattices_per_session=2, max_lattices_per_minute=10)
    await store.create(_session_request())
    first = _lattice(lattice_seq=0, utterance_id="utt-0")
    second = _lattice(lattice_seq=1, utterance_id="utt-1")
    third = _lattice(lattice_seq=2, utterance_id="utt-2")

    await store.reserve_lattice(first, TOKEN, _digest(first))
    await store.complete_lattice(first, TOKEN, _digest(first), _confident(first))
    await store.reserve_lattice(second, TOKEN, _digest(second))
    await store.complete_lattice(second, TOKEN, _digest(second), _confident(second))
    clock.advance(seconds=60)

    with pytest.raises(LatticeQuotaExceeded):
        await store.reserve_lattice(third, TOKEN, _digest(third))
    snapshot = await store.authenticate(SESSION_ID, TOKEN)
    assert snapshot.last_lattice_seq == 1
    assert snapshot.lattice_count == 2


@pytest.mark.asyncio
async def test_classifier_profile_mismatch_does_not_consume_sequence() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    mismatched_profile = ClassifierDescriptor(
        name=PROFILE.name,
        model_version="sgsl-v4",
        calibration_version=PROFILE.calibration_version,
        vocabulary_version=PROFILE.vocabulary_version,
    )
    mismatched = _lattice(classifier=mismatched_profile)

    with pytest.raises(LatticeConflict, match="classifier profile"):
        await store.reserve_lattice(mismatched, TOKEN, _digest(mismatched))
    rejected = await store.authenticate(SESSION_ID, TOKEN)
    assert rejected.last_lattice_seq is None
    assert rejected.lattice_count == 0

    valid = _lattice()
    accepted = await store.reserve_lattice(valid, TOKEN, _digest(valid))
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED


@pytest.mark.asyncio
async def test_only_one_new_lattice_can_be_in_progress_per_session() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    first = _lattice(lattice_seq=0, utterance_id="utt-0")
    second = _lattice(lattice_seq=1, utterance_id="utt-1")

    await store.reserve_lattice(first, TOKEN, _digest(first))
    with pytest.raises(LatticeInProgress, match="still being processed"):
        await store.reserve_lattice(second, TOKEN, _digest(second))

    await store.complete_lattice(first, TOKEN, _digest(first), _confident(first))
    accepted = await store.reserve_lattice(second, TOKEN, _digest(second))
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED


@pytest.mark.asyncio
async def test_active_stream_and_agent_work_block_external_session_deletion() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock)
    await store.create(_session_request())
    stream_id = uuid4()
    await store.claim_stream(
        SESSION_ID,
        TOKEN,
        stream_id,
        expected_kind=StreamKind.GLOSS_LATTICE,
    )

    with pytest.raises(InvalidSessionState, match="active stream"):
        await store.delete(SESSION_ID, TOKEN)

    lattice = _lattice()
    await store.reserve_lattice(lattice, TOKEN, _digest(lattice))
    with pytest.raises(InvalidSessionState, match="Agent processing"):
        await store.delete(SESSION_ID, TOKEN, owner_stream_id=stream_id)

    await store.complete_lattice(lattice, TOKEN, _digest(lattice), _confident(lattice))
    await store.delete(SESSION_ID, TOKEN, owner_stream_id=stream_id)
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_active_agent_reservation_survives_ttl_until_safe_completion() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    store = _store(clock, ttl_seconds=30)
    await store.create(_session_request())
    lattice = _lattice()
    digest = _digest(lattice)
    await store.reserve_lattice(lattice, TOKEN, digest)

    clock.advance(seconds=31)
    assert await store.purge_expired() == 0
    assert await store.count() == 1

    await store.complete_lattice(lattice, TOKEN, digest, _confident(lattice))
    clock.advance(seconds=31)
    assert await store.purge_expired() == 1
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_global_lattice_rate_limit_spans_sessions() -> None:
    clock = FakeClock(datetime(2026, 9, 6, tzinfo=UTC))
    session_ids = iter(
        (
            UUID("12345678-1234-5678-1234-567812345678"),
            UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        )
    )
    store = EphemeralSessionStore(
        ttl_seconds=600,
        max_lattices_per_minute=10,
        max_lattices_per_minute_global=2,
        clock=clock,
        token_factory=lambda: TOKEN,
        id_factory=lambda: next(session_ids),
    )
    first_session = await store.create(_session_request())
    second_session = await store.create(_session_request())
    first = _lattice(lattice_seq=0, utterance_id="utt-a").model_copy(
        update={"session_id": first_session.session_id}
    )
    second = _lattice(lattice_seq=0, utterance_id="utt-b").model_copy(
        update={"session_id": second_session.session_id}
    )
    third = _lattice(lattice_seq=1, utterance_id="utt-c").model_copy(
        update={"session_id": first_session.session_id}
    )

    await store.reserve_lattice(first, TOKEN, _digest(first))
    await store.complete_lattice(first, TOKEN, _digest(first), _confident(first))
    await store.reserve_lattice(second, TOKEN, _digest(second))
    await store.complete_lattice(second, TOKEN, _digest(second), _confident(second))
    with pytest.raises(LatticeRateLimited, match="global"):
        await store.reserve_lattice(third, TOKEN, _digest(third))

    clock.advance(seconds=60)
    accepted = await store.reserve_lattice(third, TOKEN, _digest(third))
    assert accepted.disposition is LatticeReservationDisposition.ACCEPTED
