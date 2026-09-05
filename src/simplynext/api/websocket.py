"""Authenticated, bounded landmark streaming over one persistent WebSocket."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Sequence
from contextlib import suppress
from time import time
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError

from simplynext.contracts import (
    AckEvent,
    ActivityEvent,
    ActivityState,
    ContractModel,
    ControlAction,
    ErrorCode,
    ErrorEvent,
    InboundStreamMessage,
    LandmarkBatch,
    LandmarkFrame,
    PongEvent,
    RepairAction,
    RepairRequiredEvent,
    SignLanguage,
    StreamControlMessage,
    StreamKind,
)
from simplynext.pipeline import (
    SegmentEvent,
    SegmentEventType,
    SegmentReason,
    UtteranceSegmenter,
)
from simplynext.runtime import RuntimeServices
from simplynext.sessions import (
    InvalidSessionToken,
    SessionExpired,
    SessionNotFound,
    SessionStoreError,
)

logger = logging.getLogger(__name__)
_MESSAGE_ADAPTER: TypeAdapter[InboundStreamMessage] = TypeAdapter(InboundStreamMessage)


async def landmark_socket(
    websocket: WebSocket,
    session_id: UUID,
) -> None:
    services: RuntimeServices = websocket.app.state.services
    token = _authorization_token(websocket.headers.get("authorization"))
    if token is None:
        await websocket.close(code=4401, reason="Bearer token required")
        return
    stream_id = uuid4()
    try:
        session = await services.sessions.claim_stream(
            session_id,
            token,
            stream_id,
            expected_kind=StreamKind.LANDMARKS,
        )
    except SessionStoreError as exc:
        await websocket.close(code=_close_code(exc), reason=exc.message)
        return

    try:
        await websocket.accept()
        services.metrics.increment("websocket_connections")
        await _send(websocket, ActivityEvent(state=ActivityState.IDLE))

        segmenter = UtteranceSegmenter()
        active_utterance_id: str | None = None
        client_drop_markers: deque[tuple[int, int]] = deque(
            maxlen=segmenter.config.max_buffered_frames
        )
        invalid_messages = 0

        while True:
            raw = await websocket.receive_text()
            if len(raw.encode("utf-8")) > services.settings.websocket_max_message_bytes:
                await _send_error(
                    websocket,
                    ErrorCode.INVALID_MESSAGE,
                    "Message exceeds the configured size limit.",
                    retryable=False,
                )
                await websocket.close(code=1009, reason="Message too large")
                return
            try:
                message = _MESSAGE_ADAPTER.validate_json(raw)
            except ValidationError:
                invalid_messages += 1
                services.metrics.increment("invalid_stream_messages")
                await _send_error(
                    websocket,
                    ErrorCode.INVALID_MESSAGE,
                    "Message does not match the negotiated schema.",
                    retryable=invalid_messages < 3,
                )
                if invalid_messages >= 3:
                    await websocket.close(code=1008, reason="Too many invalid messages")
                    return
                continue

            invalid_messages = 0
            if message.session_id != session_id:
                await _send_error(
                    websocket,
                    ErrorCode.UNAUTHORIZED,
                    "Message session_id does not match this connection.",
                    retryable=False,
                )
                await websocket.close(code=4401, reason="Session mismatch")
                return

            if isinstance(message, LandmarkBatch):
                try:
                    receipt = await services.sessions.append_batch(message, token)
                except SessionStoreError as exc:
                    if await _send_store_error(
                        websocket,
                        exc,
                        batch_seq=message.batch_seq,
                    ):
                        return
                    continue
                services.metrics.increment("landmark_batches")
                services.metrics.increment("landmark_frames", receipt.received_frames)
                services.metrics.increment("client_dropped_frames", message.dropped_before)
                services.metrics.increment("server_evicted_frames", receipt.server_evicted_frames)
                if message.dropped_before:
                    client_drop_markers.append((message.frames[0].seq, message.dropped_before))
                await _send(
                    websocket,
                    AckEvent(
                        batch_seq=receipt.batch_seq,
                        last_frame_seq=receipt.last_frame_seq,
                        received_frames=receipt.received_frames,
                        buffered_frames=receipt.buffered_frames,
                        dropped_frames=receipt.dropped_frames,
                        server_ms=_server_ms(),
                    ),
                )

                for frame in message.frames:
                    for event in segmenter.process(frame, subject_id=frame.subject_id):
                        if event.type is SegmentEventType.STARTED:
                            active_utterance_id = active_utterance_id or _utterance_id()
                            await _send(
                                websocket,
                                ActivityEvent(
                                    state=ActivityState.SIGNING,
                                    utterance_id=active_utterance_id,
                                    capture_ms=event.capture_ms,
                                ),
                            )
                        elif event.type is SegmentEventType.COMMITTED:
                            active_utterance_id = active_utterance_id or _utterance_id()
                            await _process_segment(
                                websocket,
                                services,
                                session_id,
                                token,
                                event,
                                active_utterance_id,
                                session.language,
                                _client_drops_for_frames(
                                    client_drop_markers,
                                    event.frames,
                                ),
                            )
                            _discard_drop_markers_through(
                                client_drop_markers,
                                event.frames[-1].seq,
                            )
                            active_utterance_id = None
                        elif event.type is SegmentEventType.DISCARDED:
                            utterance_id = active_utterance_id or _utterance_id()
                            await _send(
                                websocket,
                                _direct_repair(
                                    utterance_id,
                                    RepairAction.REPEAT,
                                    ("utterance_too_short",),
                                ),
                            )
                            await services.sessions.clear_live_data(session_id, token)
                            if event.frames:
                                _discard_drop_markers_through(
                                    client_drop_markers,
                                    event.frames[-1].seq,
                                )
                            active_utterance_id = None
                        elif (
                            event.type is SegmentEventType.RESET
                            and event.reason is SegmentReason.SUBJECT_CHANGED
                        ):
                            utterance_id = active_utterance_id or _utterance_id()
                            await _send(
                                websocket,
                                _direct_repair(
                                    utterance_id,
                                    RepairAction.REPOSITION,
                                    ("active_signer_changed",),
                                ),
                            )
                            await services.sessions.clear_live_data(session_id, token)
                            client_drop_markers.clear()
                            active_utterance_id = None
                continue

            assert isinstance(message, StreamControlMessage)
            if message.action is ControlAction.COMMIT:
                try:
                    await services.sessions.apply_control(message, token)
                    await services.sessions.clear_live_data(session_id, token)
                except SessionStoreError as exc:
                    if await _send_store_error(websocket, exc):
                        return
                    continue
                segment = segmenter.force_commit()
                segmenter.reset()
                utterance_id = active_utterance_id or _utterance_id()
                if segment is None or len(segment.frames) < 2:
                    await _send(
                        websocket,
                        _direct_repair(
                            utterance_id,
                            RepairAction.REPEAT,
                            ("no_signing_activity",),
                        ),
                    )
                    await _send(websocket, ActivityEvent(state=ActivityState.IDLE))
                    active_utterance_id = None
                    client_drop_markers.clear()
                    continue
                await _send(
                    websocket,
                    ActivityEvent(state=ActivityState.PROCESSING, utterance_id=utterance_id),
                )
                result = await services.translation.process_frames(
                    utterance_id=utterance_id,
                    language=session.language,
                    frames=segment.frames,
                    dropped_frames=_client_drops_for_frames(
                        client_drop_markers,
                        segment.frames,
                    ),
                )
                await _send(websocket, result)
                await _send(websocket, ActivityEvent(state=ActivityState.IDLE))
                active_utterance_id = None
                client_drop_markers.clear()
                continue

            try:
                snapshot = await services.sessions.apply_control(message, token)
            except SessionStoreError as exc:
                if await _send_store_error(websocket, exc):
                    return
                continue

            if message.action is ControlAction.PING:
                await _send(
                    websocket,
                    PongEvent(control_seq=message.control_seq, server_ms=_server_ms()),
                )
            elif message.action in {ControlAction.PAUSE, ControlAction.CLEAR_LIVE_DATA}:
                segmenter.reset()
                await services.sessions.clear_live_data(session_id, token)
                client_drop_markers.clear()
                active_utterance_id = None
                await _send(websocket, ActivityEvent(state=ActivityState.IDLE))
            elif message.action in {ControlAction.START, ControlAction.RESUME}:
                await _send(websocket, ActivityEvent(state=ActivityState.IDLE))
            elif message.action is ControlAction.END:
                pending_segment = segmenter.force_commit()
                if pending_segment is not None and len(pending_segment.frames) >= 2:
                    utterance_id = active_utterance_id or _utterance_id()
                    await _send(
                        websocket,
                        ActivityEvent(state=ActivityState.PROCESSING, utterance_id=utterance_id),
                    )
                    result = await services.translation.process_frames(
                        utterance_id=utterance_id,
                        language=snapshot.language,
                        frames=pending_segment.frames,
                        dropped_frames=_client_drops_for_frames(
                            client_drop_markers,
                            pending_segment.frames,
                        ),
                    )
                    await _send(websocket, result)
                await services.sessions.delete(
                    session_id,
                    token,
                    owner_stream_id=stream_id,
                )
                await websocket.close(code=1000, reason="Session ended")
                services.metrics.increment("sessions_ended")
                return
    except WebSocketDisconnect:
        services.metrics.increment("websocket_disconnects")
    except Exception as exc:
        services.metrics.increment("websocket_internal_errors")
        logger.exception(
            "landmark_socket_failed",
            extra={"session_id": str(session_id), "reason": type(exc).__name__},
        )
        with suppress(RuntimeError, WebSocketDisconnect):
            await _send_error(
                websocket,
                ErrorCode.INTERNAL_ERROR,
                "The stream failed safely. No caption was emitted.",
                retryable=True,
            )
    finally:
        with suppress(SessionStoreError):
            await services.sessions.release_stream(session_id, token, stream_id)


async def _process_segment(
    websocket: WebSocket,
    services: RuntimeServices,
    session_id: UUID,
    token: str,
    event: SegmentEvent,
    utterance_id: str,
    language: SignLanguage,
    dropped_frames: int,
) -> None:
    await _send(
        websocket,
        ActivityEvent(
            state=ActivityState.PROCESSING,
            utterance_id=utterance_id,
            capture_ms=event.capture_ms,
        ),
    )
    result = await services.translation.process_frames(
        utterance_id=utterance_id,
        language=language,
        frames=event.frames,
        dropped_frames=dropped_frames,
    )
    await _send(websocket, result)
    await services.sessions.clear_live_data(session_id, token)
    await _send(websocket, ActivityEvent(state=ActivityState.IDLE))


def _direct_repair(
    utterance_id: str,
    action: RepairAction,
    reason_codes: tuple[str, ...],
) -> RepairRequiredEvent:
    messages = {
        RepairAction.REPEAT: "Please repeat the sign more slowly.",
        RepairAction.REPOSITION: "Please keep both hands and shoulders visible, then try again.",
    }
    return RepairRequiredEvent(
        utterance_id=utterance_id,
        action=action,
        message=messages.get(action, "The sign could not be translated safely."),
        confidence=0.0,
        reason_codes=reason_codes,
    )


def _client_drops_for_frames(
    markers: Sequence[tuple[int, int]],
    frames: Sequence[LandmarkFrame],
) -> int:
    """Count only client-side losses adjacent to frames in one utterance window."""

    if not frames:
        return 0
    first_seq = frames[0].seq
    last_seq = frames[-1].seq
    return sum(count for before_seq, count in markers if first_seq <= before_seq <= last_seq)


def _discard_drop_markers_through(
    markers: deque[tuple[int, int]],
    last_seq: int,
) -> None:
    while markers and markers[0][0] <= last_seq:
        markers.popleft()


async def _send(websocket: WebSocket, event: ContractModel) -> None:
    await websocket.send_json(event.model_dump(mode="json"))


async def _send_error(
    websocket: WebSocket,
    code: ErrorCode,
    message: str,
    *,
    retryable: bool,
    batch_seq: int | None = None,
) -> None:
    await _send(
        websocket,
        ErrorEvent(
            code=code,
            message=message,
            retryable=retryable,
            batch_seq=batch_seq,
        ),
    )


async def _send_store_error(
    websocket: WebSocket,
    exc: SessionStoreError,
    *,
    batch_seq: int | None = None,
) -> bool:
    try:
        code = ErrorCode(exc.code)
    except ValueError:
        code = ErrorCode.INVALID_SESSION_STATE
    terminal = isinstance(
        exc,
        (InvalidSessionToken, SessionNotFound, SessionExpired),
    )
    await _send_error(
        websocket,
        code,
        exc.message,
        retryable=not terminal,
        batch_seq=batch_seq,
    )
    if terminal:
        await websocket.close(code=_close_code(exc), reason=exc.message)
    return terminal


def _authorization_token(value: str | None) -> str | None:
    if value is None:
        return None
    scheme, separator, token = value.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _close_code(exc: SessionStoreError) -> int:
    if isinstance(exc, InvalidSessionToken):
        return 4401
    if isinstance(exc, SessionNotFound):
        return 4404
    if isinstance(exc, SessionExpired):
        return 4408
    return 4409


def _server_ms() -> int:
    return round(time() * 1000)


def _utterance_id() -> str:
    return f"utt-{uuid4().hex}"
