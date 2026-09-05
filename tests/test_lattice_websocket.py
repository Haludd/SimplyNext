from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Iterator
from time import perf_counter
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from simplynext.agent import AssemblyRequest, AssemblyResult, AssemblyStatus
from simplynext.api.lattice_websocket import _handle_lattice, _safe_failure_event
from simplynext.config import Settings
from simplynext.contracts import (
    ControlAction,
    GlossLattice,
    LatticeRepairRequiredEvent,
    SessionCreateRequest,
    SignLanguage,
    StreamControlMessage,
)
from simplynext.main import create_app
from simplynext.observability import MetricsRegistry
from simplynext.orchestrator import TranslationEngine
from simplynext.recognition import ConfidencePolicy, UnconfiguredRecognizer
from simplynext.runtime import RuntimeServices
from simplynext.sessions import (
    EphemeralSessionStore,
    LatticeReservationDisposition,
)

PRODUCER = {
    "classifier_id": "frontend-temporal-classifier",
    "classifier_version": "classifier-v7",
    "confidence_kind": "calibrated_probability",
    "calibration_version": "temperature-v3",
    "vocabulary_version": "demo-v2",
}


class RecordingAssembler:
    """Deterministic Agent seam that retains every request for transport assertions."""

    ready = True

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
            source="spy_assembler",
        )


class MemoryWebSocket:
    def __init__(self, *, fail_on_processing: bool = False) -> None:
        self.events: list[dict[str, Any]] = []
        self.fail_on_processing = fail_on_processing

    async def send_json(self, payload: dict[str, Any]) -> None:
        if (
            self.fail_on_processing
            and payload.get("type") == "activity"
            and payload.get("state") == "processing"
        ):
            raise RuntimeError("simulated disconnect while delivering processing state")
        self.events.append(payload)


class ControlledTranslation:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.finish = asyncio.Event()

    async def process_lattice(
        self,
        lattice: GlossLattice,
        *,
        signer_id: str | None = None,
    ) -> LatticeRepairRequiredEvent:
        assert signer_id is None
        self.started.set()
        await self.finish.wait()
        return _safe_failure_event(lattice, "controlled_agent_result")


def _translation_with_recording_assembler() -> tuple[TranslationEngine, RecordingAssembler]:
    assembler = RecordingAssembler()
    translation = TranslationEngine(
        recognizer=UnconfiguredRecognizer(),
        policy=ConfidencePolicy(),
        assembler=assembler,
        metrics=MetricsRegistry(),
        model_language=SignLanguage.ASL,
    )
    return translation, assembler


@pytest.fixture
def harness() -> Iterator[tuple[TestClient, RecordingAssembler]]:
    translation, assembler = _translation_with_recording_assembler()
    app = create_app(
        Settings(
            environment="test",
            allowed_origins=(),
            bedrock_enabled=False,
            template_bundle_path=None,
            caption_templates_path=None,
        ),
        translation=translation,
    )
    with TestClient(app) as client:
        yield client, assembler


def _session_request(*, stream_kind: str = "gloss_lattice") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "language": "asl",
        "schema_version": "1.0",
        "stream_kind": stream_kind,
        "client": {
            "platform": "test",
            "app_version": "lattice-integration-test",
            "device_model": "virtual-frontend",
        },
        "detector": {
            "name": "mediapipe-holistic",
            "version": "frontend-test-v1",
            "delegate": "cpu",
        },
    }
    if stream_kind == "gloss_lattice":
        payload["producer"] = dict(PRODUCER)
    return payload


def _create_lattice_session(client: TestClient) -> dict[str, Any]:
    response = client.post("/v1/sessions", json=_session_request())
    assert response.status_code == 201
    return response.json()


def _authorization(session: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['stream_token']}"}


def _candidate(rank: int, gloss_id: str, confidence: float) -> dict[str, Any]:
    return {"gloss_id": gloss_id, "rank": rank, "confidence": confidence}


def _lattice(
    session: dict[str, Any],
    *,
    lattice_seq: int = 0,
    utterance_id: str = "utt-lattice-0",
    unresolved: bool = False,
) -> dict[str, Any]:
    first_slot: dict[str, Any]
    if unresolved:
        first_slot = {
            "slot_index": 0,
            "slot_id": "slot-0",
            "start_ms": 1_000,
            "end_ms": 1_300,
            "candidates": [
                _candidate(1, "HELLO", 0.62),
                _candidate(2, "BYE", 0.58),
            ],
            "resolved_gloss_id": None,
            "provenance": "unresolved",
        }
    else:
        first_slot = {
            "slot_index": 0,
            "slot_id": "slot-0",
            "start_ms": 1_000,
            "end_ms": 1_300,
            "candidates": [
                _candidate(1, "HELLO", 0.96),
                _candidate(2, "BYE", 0.40),
                _candidate(3, "THANK_YOU", 0.20),
            ],
            "resolved_gloss_id": "HELLO",
            "provenance": "classifier_high_confidence",
        }

    slots = [first_slot]
    if not unresolved:
        slots.append(
            {
                "slot_index": 1,
                "slot_id": "slot-1",
                "start_ms": 1_400,
                "end_ms": 1_750,
                "candidates": [
                    _candidate(1, "PLEASE", 0.94),
                    _candidate(2, "WATER", 0.30),
                    _candidate(3, "HELP", 0.10),
                ],
                "resolved_gloss_id": "PLEASE",
                "provenance": "classifier_high_confidence",
            }
        )

    return {
        "type": "gloss_lattice",
        "schema_version": "1.0",
        "session_id": session["session_id"],
        "lattice_seq": lattice_seq,
        "utterance_id": utterance_id,
        "language": "asl",
        "timebase": "session_monotonic_ms",
        "started_at_ms": 1_000,
        "ended_at_ms": 1_800,
        "producer": dict(PRODUCER),
        "slots": slots,
    }


def _receive_new_result(socket: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    acknowledgement = socket.receive_json()
    processing = socket.receive_json()
    result = socket.receive_json()
    idle = socket.receive_json()

    assert acknowledgement["type"] == "lattice_ack"
    assert acknowledgement["disposition"] == "accepted"
    assert processing["type"] == "activity"
    assert processing["state"] == "processing"
    assert idle["type"] == "activity"
    assert idle["state"] == "idle"
    return acknowledgement, result


async def _unit_lifecycle_setup(
    translation: Any,
    *,
    queue_timeout_seconds: float = 0.1,
) -> tuple[RuntimeServices, GlossLattice, str, bytes]:
    settings = Settings(
        environment="test",
        allowed_origins=(),
        bedrock_enabled=False,
        template_bundle_path=None,
        caption_templates_path=None,
        agent_queue_timeout_seconds=queue_timeout_seconds,
    )
    store = EphemeralSessionStore(
        max_lattices_per_session=settings.max_lattices_per_session,
        max_lattices_per_minute=settings.max_lattices_per_minute,
        max_lattices_per_minute_global=settings.max_lattices_per_minute_global,
    )
    created = await store.create(SessionCreateRequest.model_validate(_session_request()))
    session = created.model_dump(mode="json")
    lattice = GlossLattice.model_validate_json(json.dumps(_lattice(session)))
    digest = hashlib.sha256(lattice.model_dump_json().encode("utf-8")).digest()
    services = RuntimeServices(
        settings=settings,
        sessions=store,
        translation=translation,
        metrics=MetricsRegistry(),
        agent_slots=asyncio.Semaphore(1),
    )
    return services, lattice, created.stream_token, digest


def test_lattice_mode_session_negotiates_endpoint_and_hard_limits(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, _ = harness
    session = _create_lattice_session(client)

    assert session["stream_kind"] == "gloss_lattice"
    assert session["websocket_path"].endswith("/lattices")
    assert session["lattice_websocket_path"] == session["websocket_path"]
    assert session["lattice_schema_version"] == "1.0"
    assert session["max_lattice_message_bytes"] == 32_768
    assert session["max_lattice_slots"] == 64
    assert session["max_candidates_per_slot"] == 5

    missing_producer = _session_request()
    missing_producer.pop("producer")
    response = client.post("/v1/sessions", json=missing_producer)
    assert response.status_code == 422


def test_agent_only_readiness_does_not_require_legacy_recognizer(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, _ = harness

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "lattice_stream_ready"
    assert response.json()["input_modes"] == {
        "gloss_lattice": {"ready": True},
        "landmarks": {"ready": False},
    }


def test_session_stream_kind_cannot_cross_into_the_other_websocket(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, _ = harness
    lattice_session = _create_lattice_session(client)
    landmark_response = client.post(
        "/v1/sessions",
        json=_session_request(stream_kind="landmarks"),
    )
    assert landmark_response.status_code == 201
    landmark_session = landmark_response.json()

    with (
        pytest.raises(WebSocketDisconnect) as lattice_on_legacy,
        client.websocket_connect(
            f"/v1/sessions/{lattice_session['session_id']}/landmarks",
            headers=_authorization(lattice_session),
        ),
    ):
        pass
    with (
        pytest.raises(WebSocketDisconnect) as legacy_on_lattice,
        client.websocket_connect(
            f"/v1/sessions/{landmark_session['session_id']}/lattices",
            headers=_authorization(landmark_session),
        ),
    ):
        pass

    assert lattice_on_legacy.value.code == 4409
    assert legacy_on_lattice.value.code == 4409


@pytest.mark.parametrize("authorization", [None, "Bearer wrong-token"])
def test_lattice_websocket_requires_valid_session_token(
    harness: tuple[TestClient, RecordingAssembler],
    authorization: str | None,
) -> None:
    client, _ = harness
    session = _create_lattice_session(client)
    headers = {} if authorization is None else {"Authorization": authorization}

    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect(session["websocket_path"], headers=headers),
    ):
        pass

    assert closed.value.code == 4401


def test_lattice_message_session_mismatch_closes_without_agent_call(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)
    payload = _lattice(session)
    payload["session_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(payload)
        error = socket.receive_json()
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()

    assert error["code"] == "unauthorized"
    assert error["retryable"] is False
    assert closed.value.code == 4401
    assert assembler.requests == []


def test_browser_origin_is_checked_before_stream_claim() -> None:
    assembler = RecordingAssembler()
    translation = TranslationEngine(
        recognizer=UnconfiguredRecognizer(),
        policy=ConfidencePolicy(),
        assembler=assembler,
        metrics=MetricsRegistry(),
        model_language=SignLanguage.ASL,
    )
    app = create_app(
        Settings(
            environment="test",
            allowed_origins=("https://allowed.example",),
            bedrock_enabled=False,
            template_bundle_path=None,
            caption_templates_path=None,
        ),
        translation=translation,
    )

    with TestClient(app) as client:
        session = _create_lattice_session(client)
        headers = {
            **_authorization(session),
            "Origin": "https://attacker.example",
        }
        with (
            pytest.raises(WebSocketDisconnect) as closed,
            client.websocket_connect(session["websocket_path"], headers=headers),
        ):
            pass

    assert closed.value.code == 4403
    assert assembler.requests == []


def test_valid_lattice_event_order_and_complete_top_k_reach_agent(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)
    lattice = _lattice(session)

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(lattice)
        acknowledgement, result = _receive_new_result(socket)

    assert acknowledgement["lattice_seq"] == 0
    assert acknowledgement["utterance_id"] == "utt-lattice-0"
    assert "revision" not in acknowledgement
    assert result["type"] == "lattice_result"
    assert result["status"] == "confident"
    assert result["caption"] == "Hello, please."
    assert result["tts_text"] == "Hello, please."
    assert result["gloss_id_trace"] == ["HELLO", "PLEASE"]
    assert result["classifier_version"] == PRODUCER["classifier_version"]
    assert "revision" not in result
    assert [item["slot_id"] for item in result["evidence_trace"]] == ["slot-0", "slot-1"]
    assert [item["resolved_gloss_id"] for item in result["evidence_trace"]] == [
        "HELLO",
        "PLEASE",
    ]
    assert [len(item["candidates"]) for item in result["evidence_trace"]] == [3, 3]

    assert len(assembler.requests) == 1
    request = assembler.requests[0]
    assert request.lattice_seq == 0
    assert request.signer_id is None
    assert request.classifier_version == PRODUCER["classifier_version"]
    assert request.calibration_version == PRODUCER["calibration_version"]
    assert request.vocabulary_version == PRODUCER["vocabulary_version"]
    assert tuple(item.gloss_id for item in request.evidence) == ("HELLO", "PLEASE")
    assert tuple(item.provenance for item in request.evidence) == (
        "classifier_high_confidence",
        "classifier_high_confidence",
    )
    assert tuple(item.gloss_id for item in request.evidence[0].candidates) == (
        "HELLO",
        "BYE",
        "THANK_YOU",
    )
    assert tuple(item.confidence for item in request.evidence[1].candidates) == (
        0.94,
        0.30,
        0.10,
    )


def test_unresolved_slot_fails_closed_without_calling_agent(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(_lattice(session, unresolved=True))
        _, repair = _receive_new_result(socket)

    assert repair["type"] == "lattice_repair_required"
    assert repair["status"] == "uncertain"
    assert repair["action"] == "choose_candidate"
    assert repair["target_slot_ids"] == ["slot-0"]
    assert repair["reason_codes"] == ["unresolved_lattice_slot"]
    assert [choice["gloss_id"] for choice in repair["choices"]] == ["HELLO", "BYE"]
    assert "caption" not in repair
    assert "tts_text" not in repair
    assert assembler.requests == []


def test_exact_retry_returns_cached_result_without_second_agent_call(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)
    lattice = _lattice(session)

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(lattice)
        _, first_result = _receive_new_result(socket)

        socket.send_json(lattice)
        cached_ack = socket.receive_json()
        cached_result = socket.receive_json()
        idle = socket.receive_json()

    assert first_result["type"] == "lattice_result"
    assert cached_ack["type"] == "lattice_ack"
    assert cached_ack["disposition"] == "cached"
    assert cached_result == first_result
    assert idle["type"] == "activity"
    assert idle["state"] == "idle"
    assert len(assembler.requests) == 1


def test_conflicting_retry_and_stale_sequence_are_rejected_without_agent_calls(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)
    first = _lattice(session, lattice_seq=2)

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(first)
        _receive_new_result(socket)

        conflict = _lattice(
            session,
            lattice_seq=2,
            utterance_id="different-utterance",
        )
        socket.send_json(conflict)
        conflict_error = socket.receive_json()

        stale = _lattice(session, lattice_seq=1, utterance_id="utt-stale")
        socket.send_json(stale)
        stale_error = socket.receive_json()

    assert conflict_error["type"] == "error"
    assert conflict_error["code"] == "invalid_session_state"
    assert conflict_error["retryable"] is False
    assert "different content" in conflict_error["message"]
    assert stale_error["type"] == "error"
    assert stale_error["code"] == "non_monotonic_sequence"
    assert stale_error["retryable"] is False
    assert "greater than 2" in stale_error["message"]
    assert len(assembler.requests) == 1


def test_lattice_socket_ping_and_end_delete_the_session(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, _ = harness
    session = _create_lattice_session(client)
    session_id = UUID(session["session_id"])

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=0,
                action=ControlAction.PING,
                client_ms=900,
            ).model_dump(mode="json")
        )
        pong = socket.receive_json()
        assert pong["type"] == "pong"
        assert pong["control_seq"] == 0

        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=1,
                action=ControlAction.END,
            ).model_dump(mode="json")
        )
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()

    assert closed.value.code == 1000
    response = client.delete(
        f"/v1/sessions/{session['session_id']}",
        headers=_authorization(session),
    )
    assert response.status_code == 404


def test_http_delete_cannot_race_an_active_lattice_socket(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, _ = harness
    session = _create_lattice_session(client)
    delete_path = f"/v1/sessions/{session['session_id']}"

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        rejected = client.delete(delete_path, headers=_authorization(session))
        assert rejected.status_code == 409
        assert "active stream" in rejected.json()["detail"]

    deleted = client.delete(delete_path, headers=_authorization(session))
    assert deleted.status_code == 204


def test_malformed_raw_landmark_and_binary_messages_fail_protocol_safely(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)
    lattice_with_raw_data = _lattice(session)
    lattice_with_raw_data["landmarks"] = [[0.1, 0.2, 0.0, 0.99]]

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"

        socket.send_json(lattice_with_raw_data)
        raw_error = socket.receive_json()
        assert raw_error["type"] == "error"
        assert raw_error["code"] == "invalid_message"
        assert raw_error["retryable"] is True

        socket.send_bytes(b"not-json-and-not-allowed")
        binary_error = socket.receive_json()
        assert binary_error["type"] == "error"
        assert binary_error["code"] == "invalid_message"
        assert binary_error["retryable"] is True
        assert "Binary" in binary_error["message"]

        socket.send_json(
            {
                "type": "landmark_batch",
                "session_id": session["session_id"],
                "batch_seq": 0,
                "frames": [],
            }
        )
        third_error = socket.receive_json()
        assert third_error["type"] == "error"
        assert third_error["code"] == "invalid_message"
        assert third_error["retryable"] is False
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()

    assert closed.value.code == 1008
    assert assembler.requests == []


def test_three_schema_valid_but_forbidden_controls_close_policy_violation(
    harness: tuple[TestClient, RecordingAssembler],
) -> None:
    client, assembler = harness
    session = _create_lattice_session(client)

    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        for control_seq in range(3):
            socket.send_json(
                StreamControlMessage(
                    session_id=session["session_id"],
                    control_seq=control_seq,
                    action=ControlAction.START,
                ).model_dump(mode="json")
            )
            error = socket.receive_json()
            assert error["code"] == "invalid_message"
            assert error["retryable"] is (control_seq < 2)
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()

    assert closed.value.code == 1008
    assert assembler.requests == []


def test_oversized_lattice_message_returns_error_then_closes_1009() -> None:
    assembler = RecordingAssembler()
    metrics = MetricsRegistry()
    translation = TranslationEngine(
        recognizer=UnconfiguredRecognizer(),
        policy=ConfidencePolicy(),
        assembler=assembler,
        metrics=metrics,
        model_language=SignLanguage.ASL,
    )
    app = create_app(
        Settings(
            environment="test",
            allowed_origins=(),
            bedrock_enabled=False,
            template_bundle_path=None,
            caption_templates_path=None,
        ),
        translation=translation,
    )

    with TestClient(app) as client:
        session = _create_lattice_session(client)
        with client.websocket_connect(
            session["websocket_path"], headers=_authorization(session)
        ) as socket:
            assert socket.receive_json()["state"] == "idle"
            socket.send_text("x" * 32_769)
            error = socket.receive_json()
            assert error["type"] == "error"
            assert error["code"] == "invalid_message"
            assert error["retryable"] is False
            assert "size limit" in error["message"]
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_json()

    assert closed.value.code == 1009
    assert assembler.requests == []


def test_ctr_v1_settings_reject_a_deployment_specific_message_limit() -> None:
    with pytest.raises(ValidationError):
        Settings(gloss_lattice_max_message_bytes=32_767)


@pytest.mark.asyncio
async def test_stale_sequence_is_rejected_before_waiting_for_agent_capacity() -> None:
    translation, assembler = _translation_with_recording_assembler()
    services, lattice, token, _ = await _unit_lifecycle_setup(translation)
    accepted = lattice.model_copy(update={"lattice_seq": 2, "utterance_id": "utterance-2"})
    accepted_digest = hashlib.sha256(accepted.model_dump_json().encode("utf-8")).digest()
    await services.sessions.reserve_lattice(accepted, token, accepted_digest)
    await services.sessions.complete_lattice(
        accepted,
        token,
        accepted_digest,
        _safe_failure_event(accepted, "test-complete"),
    )
    stale = lattice.model_copy(update={"lattice_seq": 1, "utterance_id": "utterance-1"})
    stale_digest = hashlib.sha256(stale.model_dump_json().encode("utf-8")).digest()
    websocket = MemoryWebSocket()
    await services.agent_slots.acquire()

    try:
        keep_open = await _handle_lattice(
            websocket=websocket,  # type: ignore[arg-type]
            services=services,
            lattice=stale,
            token=token,
            payload_digest=stale_digest,
            byte_count=len(stale.model_dump_json().encode("utf-8")),
            validation_started=perf_counter(),
        )
    finally:
        services.agent_slots.release()

    assert keep_open is True
    assert websocket.events[-1]["type"] == "error"
    assert websocket.events[-1]["code"] == "non_monotonic_sequence"
    assert websocket.events[-1]["retryable"] is False
    assert assembler.requests == []


@pytest.mark.asyncio
async def test_agent_queue_timeout_does_not_consume_lattice_sequence() -> None:
    translation, _ = _translation_with_recording_assembler()
    services, lattice, token, digest = await _unit_lifecycle_setup(translation)
    websocket = MemoryWebSocket()
    await services.agent_slots.acquire()

    try:
        keep_open = await _handle_lattice(
            websocket=websocket,  # type: ignore[arg-type]
            services=services,
            lattice=lattice,
            token=token,
            payload_digest=digest,
            byte_count=len(lattice.model_dump_json().encode("utf-8")),
            validation_started=perf_counter(),
        )
    finally:
        services.agent_slots.release()

    assert keep_open is True
    assert websocket.events[-1]["type"] == "error"
    assert websocket.events[-1]["code"] == "rate_limited"
    assert websocket.events[-1]["retryable"] is True
    reservation = await services.sessions.reserve_lattice(lattice, token, digest)
    assert reservation.disposition is LatticeReservationDisposition.ACCEPTED


@pytest.mark.asyncio
async def test_cached_retry_bypasses_saturated_agent_queue() -> None:
    translation, assembler = _translation_with_recording_assembler()
    services, lattice, token, digest = await _unit_lifecycle_setup(translation)
    terminal = _safe_failure_event(lattice, "cached_test_result")
    await services.sessions.reserve_lattice(lattice, token, digest)
    await services.sessions.complete_lattice(lattice, token, digest, terminal)
    await services.agent_slots.acquire()
    websocket = MemoryWebSocket()

    try:
        keep_open = await _handle_lattice(
            websocket=websocket,  # type: ignore[arg-type]
            services=services,
            lattice=lattice,
            token=token,
            payload_digest=digest,
            byte_count=len(lattice.model_dump_json().encode("utf-8")),
            validation_started=perf_counter(),
        )
    finally:
        services.agent_slots.release()

    assert keep_open is True
    assert [event["type"] for event in websocket.events] == [
        "lattice_ack",
        "lattice_repair_required",
        "activity",
    ]
    assert websocket.events[0]["disposition"] == "cached"
    assert websocket.events[1]["reason_codes"] == ["cached_test_result"]
    assert assembler.requests == []


@pytest.mark.asyncio
async def test_send_failure_after_ack_caches_safe_terminal_event() -> None:
    translation, assembler = _translation_with_recording_assembler()
    services, lattice, token, digest = await _unit_lifecycle_setup(translation)
    websocket = MemoryWebSocket(fail_on_processing=True)

    with pytest.raises(RuntimeError, match="simulated disconnect"):
        await _handle_lattice(
            websocket=websocket,  # type: ignore[arg-type]
            services=services,
            lattice=lattice,
            token=token,
            payload_digest=digest,
            byte_count=len(lattice.model_dump_json().encode("utf-8")),
            validation_started=perf_counter(),
        )

    replay = await services.sessions.reserve_lattice(lattice, token, digest)
    assert replay.disposition is LatticeReservationDisposition.CACHED
    assert isinstance(replay.cached_event, LatticeRepairRequiredEvent)
    assert replay.cached_event.reason_codes == ("agent_delivery_interrupted",)
    assert assembler.requests == []
    assert services.agent_slots.locked() is False


@pytest.mark.asyncio
async def test_cancellation_holds_agent_slot_until_underlying_work_finishes() -> None:
    translation = ControlledTranslation()
    services, lattice, token, digest = await _unit_lifecycle_setup(translation)
    websocket = MemoryWebSocket()
    handler = asyncio.create_task(
        _handle_lattice(
            websocket=websocket,  # type: ignore[arg-type]
            services=services,
            lattice=lattice,
            token=token,
            payload_digest=digest,
            byte_count=len(lattice.model_dump_json().encode("utf-8")),
            validation_started=perf_counter(),
        )
    )
    await translation.started.wait()

    handler.cancel()
    await asyncio.sleep(0)
    assert handler.done() is False
    assert services.agent_slots.locked() is True

    translation.finish.set()
    with pytest.raises(asyncio.CancelledError):
        await handler

    assert services.agent_slots.locked() is False
    replay = await services.sessions.reserve_lattice(lattice, token, digest)
    assert replay.disposition is LatticeReservationDisposition.CACHED
    assert isinstance(replay.cached_event, LatticeRepairRequiredEvent)
    assert replay.cached_event.reason_codes == ("controlled_agent_result",)
