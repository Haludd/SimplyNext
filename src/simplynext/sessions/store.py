"""Thread-safe in-memory storage for ephemeral live recognition sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4

from simplynext.contracts import (
    ControlAction,
    LandmarkBatch,
    LandmarkFrame,
    SessionCreateRequest,
    SessionCreateResponse,
    SignLanguage,
    StreamControlMessage,
)


class SessionState(StrEnum):
    READY = "ready"
    STREAMING = "streaming"
    PAUSED = "paused"
    ENDED = "ended"


class SessionStoreError(Exception):
    """Base exception with a stable machine-readable code."""

    code = "session_store_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SessionNotFound(SessionStoreError):
    code = "session_not_found"


class InvalidSessionToken(SessionStoreError):
    code = "unauthorized"


class SessionExpired(SessionStoreError):
    code = "session_expired"


class InvalidSessionState(SessionStoreError):
    code = "invalid_session_state"


class NonMonotonicSequence(SessionStoreError):
    code = "non_monotonic_sequence"


class BatchTooLarge(SessionStoreError):
    code = "batch_too_large"


class TooManySessions(SessionStoreError):
    code = "rate_limited"


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    session_id: UUID
    language: SignLanguage
    state: SessionState
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    last_batch_seq: int | None
    last_frame_seq: int | None
    last_capture_ms: int | None
    last_control_seq: int | None
    buffered_frames: int
    total_frames_received: int
    client_dropped_frames: int
    server_evicted_frames: int


@dataclass(frozen=True, slots=True)
class IngestReceipt:
    session_id: UUID
    batch_seq: int
    last_frame_seq: int
    received_frames: int
    buffered_frames: int
    client_dropped_frames: int
    server_evicted_frames: int

    @property
    def dropped_frames(self) -> int:
        return self.client_dropped_frames + self.server_evicted_frames


@dataclass(slots=True)
class _SessionRecord:
    session_id: UUID
    token_digest: bytes
    request: SessionCreateRequest
    state: SessionState
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    frames: deque[LandmarkFrame]
    last_batch_seq: int = -1
    last_frame_seq: int = -1
    last_capture_ms: int = -1
    last_control_seq: int = -1
    total_frames_received: int = 0
    client_dropped_frames: int = 0
    server_evicted_frames: int = 0
    active_stream_id: UUID | None = None


class EphemeralSessionStore:
    """Bounded live-session state with no persistence or plaintext token storage.

    Public methods are asynchronous for direct use by FastAPI handlers. A
    ``threading.RLock`` protects the underlying records as well, so multiple event
    loops or worker threads cannot interleave mutations inside one process.
    """

    def __init__(
        self,
        *,
        ttl_seconds: int = 900,
        buffer_frames: int = 600,
        max_batch_frames: int = 8,
        target_fps: int = 20,
        max_sessions: int = 128,
        websocket_path_template: str = "/v1/sessions/{session_id}/landmarks",
        clock: Callable[[], datetime] | None = None,
        token_factory: Callable[[], str] | None = None,
        id_factory: Callable[[], UUID] | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if buffer_frames <= 0:
            raise ValueError("buffer_frames must be positive")
        if not 1 <= max_batch_frames <= 32:
            raise ValueError("max_batch_frames must be between 1 and 32")
        if not 1 <= target_fps <= 60:
            raise ValueError("target_fps must be between 1 and 60")
        if max_sessions < 1:
            raise ValueError("max_sessions must be positive")
        if "{session_id}" not in websocket_path_template:
            raise ValueError("websocket_path_template must contain {session_id}")

        self._ttl = timedelta(seconds=ttl_seconds)
        self._buffer_frames = buffer_frames
        self._max_batch_frames = max_batch_frames
        self._target_fps = target_fps
        self._max_sessions = max_sessions
        self._websocket_path_template = websocket_path_template
        self._clock = clock or (lambda: datetime.now(UTC))
        self._token_factory = token_factory or (lambda: secrets.token_urlsafe(32))
        self._id_factory = id_factory or uuid4
        self._records: dict[UUID, _SessionRecord] = {}
        self._lock = RLock()

    async def create(self, request: SessionCreateRequest) -> SessionCreateResponse:
        """Create a session and return its token exactly once."""

        now = self._now()
        session_id = self._id_factory()
        token = self._token_factory()
        if len(token) < 32:
            raise ValueError("token_factory must return at least 32 characters")
        record = _SessionRecord(
            session_id=session_id,
            token_digest=self._token_digest(token),
            request=request,
            state=SessionState.READY,
            created_at=now,
            last_seen_at=now,
            expires_at=now + self._ttl,
            frames=deque(maxlen=self._buffer_frames),
        )
        with self._lock:
            self._purge_expired_locked(now)
            if len(self._records) >= self._max_sessions:
                raise TooManySessions("maximum number of active sessions reached")
            if session_id in self._records:
                raise ValueError("id_factory returned an existing session_id")
            self._records[session_id] = record

        return SessionCreateResponse(
            session_id=session_id,
            stream_token=token,
            websocket_path=self._websocket_path_template.format(session_id=session_id),
            created_at=now,
            expires_at=record.expires_at,
            max_batch_frames=self._max_batch_frames,
            target_fps=self._target_fps,
        )

    async def create_session(self, request: SessionCreateRequest) -> SessionCreateResponse:
        """Explicit alias used by route modules."""

        return await self.create(request)

    async def authenticate(
        self,
        session_id: UUID | str,
        token: str,
        *,
        touch: bool = True,
    ) -> SessionSnapshot:
        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=touch)
            return self._snapshot(record)

    async def claim_stream(
        self,
        session_id: UUID | str,
        token: str,
        stream_id: UUID,
    ) -> SessionSnapshot:
        """Exclusively bind one live WebSocket to a session."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=True)
            if record.active_stream_id not in (None, stream_id):
                raise InvalidSessionState("session already has an active landmark stream")
            record.active_stream_id = stream_id
            return self._snapshot(record)

    async def release_stream(
        self,
        session_id: UUID | str,
        token: str,
        stream_id: UUID,
    ) -> bool:
        """Release and erase data only when called by the owning WebSocket."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=False)
            if record.active_stream_id != stream_id:
                return False
            record.active_stream_id = None
            record.frames.clear()
            return True

    async def append_batch(self, batch: LandmarkBatch, token: str) -> IngestReceipt:
        """Validate and atomically append one ordered landmark batch."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(batch.session_id, token, now, touch=True)
            if record.state is SessionState.PAUSED:
                raise InvalidSessionState("cannot append landmarks while session is paused")
            if record.state is SessionState.ENDED:
                raise InvalidSessionState("cannot append landmarks after session end")
            if len(batch.frames) > self._max_batch_frames:
                raise BatchTooLarge(
                    f"batch has {len(batch.frames)} frames; maximum is {self._max_batch_frames}"
                )
            if batch.batch_seq <= record.last_batch_seq:
                raise NonMonotonicSequence(
                    f"batch_seq must be greater than {record.last_batch_seq}"
                )

            first = batch.frames[0]
            if first.seq <= record.last_frame_seq:
                raise NonMonotonicSequence(
                    f"frame seq must be greater than {record.last_frame_seq}"
                )
            if first.capture_ms <= record.last_capture_ms:
                raise NonMonotonicSequence(
                    f"capture_ms must be greater than {record.last_capture_ms}"
                )

            evicted = max(
                0,
                len(record.frames) + len(batch.frames) - self._buffer_frames,
            )
            record.frames.extend(batch.frames)
            record.last_batch_seq = batch.batch_seq
            record.last_frame_seq = batch.frames[-1].seq
            record.last_capture_ms = batch.frames[-1].capture_ms
            record.total_frames_received += len(batch.frames)
            record.client_dropped_frames += batch.dropped_before
            record.server_evicted_frames += evicted
            if record.state is SessionState.READY:
                record.state = SessionState.STREAMING

            return IngestReceipt(
                session_id=record.session_id,
                batch_seq=batch.batch_seq,
                last_frame_seq=record.last_frame_seq,
                received_frames=len(batch.frames),
                buffered_frames=len(record.frames),
                client_dropped_frames=batch.dropped_before,
                server_evicted_frames=evicted,
            )

    async def apply_control(
        self,
        message: StreamControlMessage,
        token: str,
    ) -> SessionSnapshot:
        """Apply an ordered session-state transition."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(message.session_id, token, now, touch=True)
            if message.control_seq <= record.last_control_seq:
                raise NonMonotonicSequence(
                    f"control_seq must be greater than {record.last_control_seq}"
                )

            action = message.action
            if action is ControlAction.START:
                if record.state not in (SessionState.READY, SessionState.STREAMING):
                    raise InvalidSessionState("start requires a ready or streaming session")
                record.state = SessionState.STREAMING
            elif action is ControlAction.PAUSE:
                if record.state is not SessionState.STREAMING:
                    raise InvalidSessionState("pause requires a streaming session")
                record.state = SessionState.PAUSED
            elif action is ControlAction.RESUME:
                if record.state is not SessionState.PAUSED:
                    raise InvalidSessionState("resume requires a paused session")
                record.state = SessionState.STREAMING
            elif action is ControlAction.COMMIT:
                if record.state is not SessionState.STREAMING:
                    raise InvalidSessionState("commit requires a streaming session")
            elif action is ControlAction.END:
                if record.state is SessionState.ENDED:
                    raise InvalidSessionState("session is already ended")
                record.state = SessionState.ENDED
                record.frames.clear()
            elif action is ControlAction.CLEAR_LIVE_DATA:
                record.frames.clear()
            elif action is ControlAction.PING:
                if record.state is SessionState.ENDED:
                    raise InvalidSessionState("session is ended")

            record.last_control_seq = message.control_seq
            return self._snapshot(record)

    async def get_live_frames(
        self,
        session_id: UUID | str,
        token: str,
    ) -> tuple[LandmarkFrame, ...]:
        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=True)
            return tuple(record.frames)

    async def clear_live_data(self, session_id: UUID | str, token: str) -> int:
        """Erase buffered landmarks while preserving anti-replay sequence state."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=True)
            cleared = len(record.frames)
            record.frames.clear()
            return cleared

    async def delete(self, session_id: UUID | str, token: str) -> None:
        """Erase all in-memory state for an authenticated session."""

        now = self._now()
        with self._lock:
            record = self._authorized_record(session_id, token, now, touch=False)
            record.frames.clear()
            del self._records[record.session_id]

    async def purge_expired(self) -> int:
        """Erase every expired session and return the number removed."""

        now = self._now()
        with self._lock:
            return self._purge_expired_locked(now)

    async def count(self) -> int:
        with self._lock:
            return len(self._records)

    def _authorized_record(
        self,
        session_id: UUID | str,
        token: str,
        now: datetime,
        *,
        touch: bool,
    ) -> _SessionRecord:
        canonical_id = self._canonical_id(session_id)
        record = self._records.get(canonical_id)
        if record is None:
            raise SessionNotFound("session does not exist")
        if now >= record.expires_at:
            record.frames.clear()
            del self._records[canonical_id]
            raise SessionExpired("session has expired")
        if not isinstance(token, str) or not hmac.compare_digest(
            record.token_digest,
            self._token_digest(token),
        ):
            raise InvalidSessionToken("stream token is invalid")
        if touch:
            record.last_seen_at = now
            record.expires_at = now + self._ttl
        return record

    def _purge_expired_locked(self, now: datetime) -> int:
        expired_ids = [
            session_id for session_id, record in self._records.items() if now >= record.expires_at
        ]
        for session_id in expired_ids:
            self._records[session_id].frames.clear()
            del self._records[session_id]
        return len(expired_ids)

    @staticmethod
    def _canonical_id(session_id: UUID | str) -> UUID:
        if isinstance(session_id, UUID):
            return session_id
        try:
            return UUID(str(session_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise SessionNotFound("session does not exist") from exc

    @staticmethod
    def _token_digest(token: str) -> bytes:
        if not isinstance(token, str):
            return b""
        return hashlib.sha256(token.encode("utf-8")).digest()

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    @staticmethod
    def _snapshot(record: _SessionRecord) -> SessionSnapshot:
        return SessionSnapshot(
            session_id=record.session_id,
            language=record.request.language,
            state=record.state,
            created_at=record.created_at,
            last_seen_at=record.last_seen_at,
            expires_at=record.expires_at,
            last_batch_seq=None if record.last_batch_seq < 0 else record.last_batch_seq,
            last_frame_seq=None if record.last_frame_seq < 0 else record.last_frame_seq,
            last_capture_ms=None if record.last_capture_ms < 0 else record.last_capture_ms,
            last_control_seq=None if record.last_control_seq < 0 else record.last_control_seq,
            buffered_frames=len(record.frames),
            total_frames_received=record.total_frames_received,
            client_dropped_frames=record.client_dropped_frames,
            server_evicted_frames=record.server_evicted_frames,
        )
