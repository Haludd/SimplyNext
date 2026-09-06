from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from simplynext.contracts import (
    HAND_LANDMARK_NAMES,
    CameraGeometry,
    ClientDescriptor,
    ClientPlatform,
    ControlAction,
    DetectorDescriptor,
    LandmarkBatch,
    LandmarkFrame,
    SessionCreateRequest,
    StreamControlMessage,
)
from simplynext.sessions import (
    EphemeralSessionStore,
    InvalidSessionState,
    InvalidSessionToken,
    NonMonotonicSequence,
    SessionExpired,
    SessionState,
)

SESSION_ID = UUID("12345678-1234-5678-1234-567812345678")
TOKEN = "test-token-which-is-at-least-thirty-two-characters"


@dataclass
class FakeClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def request() -> SessionCreateRequest:
    return SessionCreateRequest(
        language="sgsl",
        stream_kind="landmarks",
        client=ClientDescriptor(platform=ClientPlatform.TEST, app_version="test"),
        detector=DetectorDescriptor(name="test-detector", version="1"),
    )


def landmark_frame(seq: int, capture_ms: int) -> LandmarkFrame:
    point = (0.2, 0.3, -0.1, 0.95)
    return LandmarkFrame(
        seq=seq,
        capture_ms=capture_ms,
        left_hand=tuple(point for _ in HAND_LANDMARK_NAMES),
        left_hand_score=0.9,
    )


def batch(
    *,
    batch_seq: int,
    frame_seq: int,
    capture_ms: int,
    dropped_before: int = 0,
) -> LandmarkBatch:
    return LandmarkBatch(
        session_id=SESSION_ID,
        batch_seq=batch_seq,
        camera=CameraGeometry(
            source_width=640,
            source_height=480,
            rotation_degrees=0,
            mirrored_input=True,
        ),
        frames=(landmark_frame(frame_seq, capture_ms),),
        dropped_before=dropped_before,
    )


def make_store(clock: FakeClock, *, buffer_frames: int = 2) -> EphemeralSessionStore:
    return EphemeralSessionStore(
        ttl_seconds=30,
        buffer_frames=buffer_frames,
        max_batch_frames=2,
        clock=clock,
        token_factory=lambda: TOKEN,
        id_factory=lambda: SESSION_ID,
    )


def test_session_authentication_buffering_and_clear_preserve_replay_guard() -> None:
    async def scenario() -> None:
        clock = FakeClock(datetime(2026, 9, 5, tzinfo=UTC))
        store = make_store(clock)
        created = await store.create(request())
        assert created.stream_token == TOKEN
        assert str(created.session_id) in created.websocket_path

        with pytest.raises(InvalidSessionToken):
            await store.authenticate(created.session_id, "x" * 40)

        first = await store.append_batch(
            batch(batch_seq=0, frame_seq=10, capture_ms=100, dropped_before=1),
            TOKEN,
        )
        assert first.received_frames == 1
        assert first.dropped_frames == 1

        await store.append_batch(batch(batch_seq=1, frame_seq=11, capture_ms=110), TOKEN)
        third = await store.append_batch(batch(batch_seq=2, frame_seq=12, capture_ms=120), TOKEN)
        assert third.server_evicted_frames == 1
        assert [item.seq for item in await store.get_live_frames(SESSION_ID, TOKEN)] == [11, 12]

        assert await store.clear_live_data(SESSION_ID, TOKEN) == 2
        assert await store.get_live_frames(SESSION_ID, TOKEN) == ()
        with pytest.raises(NonMonotonicSequence):
            await store.append_batch(batch(batch_seq=3, frame_seq=12, capture_ms=130), TOKEN)

    asyncio.run(scenario())


def test_control_state_machine_erases_frames_on_end() -> None:
    async def scenario() -> None:
        clock = FakeClock(datetime(2026, 9, 5, tzinfo=UTC))
        store = make_store(clock)
        await store.create(request())

        started = await store.apply_control(
            StreamControlMessage(
                session_id=SESSION_ID,
                control_seq=0,
                action=ControlAction.START,
            ),
            TOKEN,
        )
        assert started.state is SessionState.STREAMING
        await store.append_batch(batch(batch_seq=0, frame_seq=0, capture_ms=100), TOKEN)

        paused = await store.apply_control(
            StreamControlMessage(
                session_id=SESSION_ID,
                control_seq=1,
                action=ControlAction.PAUSE,
            ),
            TOKEN,
        )
        assert paused.state is SessionState.PAUSED
        with pytest.raises(InvalidSessionState):
            await store.append_batch(batch(batch_seq=1, frame_seq=1, capture_ms=110), TOKEN)

        await store.apply_control(
            StreamControlMessage(
                session_id=SESSION_ID,
                control_seq=2,
                action=ControlAction.RESUME,
            ),
            TOKEN,
        )
        ended = await store.apply_control(
            StreamControlMessage(
                session_id=SESSION_ID,
                control_seq=3,
                action=ControlAction.END,
            ),
            TOKEN,
        )
        assert ended.state is SessionState.ENDED
        assert ended.buffered_frames == 0

    asyncio.run(scenario())


def test_idle_ttl_renews_then_erases_expired_session() -> None:
    async def scenario() -> None:
        clock = FakeClock(datetime(2026, 9, 5, tzinfo=UTC))
        store = make_store(clock)
        await store.create(request())

        clock.advance(seconds=20)
        renewed = await store.authenticate(SESSION_ID, TOKEN)
        assert renewed.expires_at == clock.value + timedelta(seconds=30)

        clock.advance(seconds=20)
        assert (await store.authenticate(SESSION_ID, TOKEN)).session_id == SESSION_ID

        clock.advance(seconds=31)
        with pytest.raises(SessionExpired):
            await store.authenticate(SESSION_ID, TOKEN)
        assert await store.count() == 0

    asyncio.run(scenario())


def test_purge_expired_removes_untouched_sessions() -> None:
    async def scenario() -> None:
        clock = FakeClock(datetime(2026, 9, 5, tzinfo=UTC))
        store = make_store(clock)
        await store.create(request())
        clock.advance(seconds=30)
        assert await store.purge_expired() == 1
        assert await store.count() == 0

    asyncio.run(scenario())
