from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from simplynext.api.websocket import _client_drops_for_frames
from simplynext.config import Settings
from simplynext.contracts import (
    FACE_LANDMARK_NAMES,
    HAND_LANDMARK_NAMES,
    POSE_LANDMARK_NAMES,
    CameraGeometry,
    ControlAction,
    LandmarkBatch,
    LandmarkFrame,
    StreamControlMessage,
)
from simplynext.main import create_app

Point = tuple[float, float, float, float]


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            allowed_origins=(),
            bedrock_enabled=False,
            template_bundle_path=None,
            caption_templates_path=None,
        )
    )
    with TestClient(app) as test_client:
        yield test_client


def _create_session(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/v1/sessions",
        json={
            "language": "asl",
            "schema_version": "1.0",
            "client": {
                "platform": "test",
                "app_version": "integration-test",
                "device_model": "virtual-camera",
            },
            "detector": {
                "name": "mediapipe-holistic",
                "version": "test-fixture-1",
                "delegate": "cpu",
            },
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert len(payload["stream_token"]) >= 32
    assert payload["websocket_path"].endswith("/landmarks")
    assert len(payload["layout"]["hand"]) == 21
    assert len(payload["layout"]["pose"]) == 9
    assert len(payload["layout"]["face"]) == 16
    return payload


def _point(x: float, y: float, z: float = 0.0, confidence: float = 0.96) -> Point:
    return (x, y, z, confidence)


def _pose(hand_offset: float) -> tuple[Point, ...]:
    coordinates = {
        "nose": _point(0.50, 0.20, -0.03),
        "left_shoulder": _point(0.41, 0.40, 0.01),
        "right_shoulder": _point(0.59, 0.40, 0.01),
        "left_elbow": _point(0.37, 0.49, 0.00),
        "right_elbow": _point(0.63, 0.49, 0.00),
        "left_wrist": _point(0.39 + hand_offset, 0.34, -0.02),
        "right_wrist": _point(0.61 - hand_offset, 0.34, -0.02),
        "left_hip": _point(0.45, 0.69, 0.02),
        "right_hip": _point(0.55, 0.69, 0.02),
    }
    return tuple(coordinates[name] for name in POSE_LANDMARK_NAMES)


def _hand(wrist_x: float, *, direction: float) -> tuple[Point, ...]:
    coordinates = {
        "wrist": _point(wrist_x, 0.34, -0.02),
        "thumb_cmc": _point(wrist_x + direction * 0.018, 0.325, -0.021),
        "thumb_mcp": _point(wrist_x + direction * 0.032, 0.305, -0.023),
        "thumb_ip": _point(wrist_x + direction * 0.044, 0.284, -0.025),
        "thumb_tip": _point(wrist_x + direction * 0.055, 0.264, -0.027),
        "index_mcp": _point(wrist_x + direction * 0.020, 0.294, -0.020),
        "index_pip": _point(wrist_x + direction * 0.022, 0.257, -0.022),
        "index_dip": _point(wrist_x + direction * 0.023, 0.230, -0.024),
        "index_tip": _point(wrist_x + direction * 0.024, 0.205, -0.025),
        "middle_mcp": _point(wrist_x, 0.289, -0.019),
        "middle_pip": _point(wrist_x, 0.247, -0.021),
        "middle_dip": _point(wrist_x, 0.218, -0.023),
        "middle_tip": _point(wrist_x, 0.190, -0.024),
        "ring_mcp": _point(wrist_x - direction * 0.018, 0.296, -0.018),
        "ring_pip": _point(wrist_x - direction * 0.020, 0.258, -0.020),
        "ring_dip": _point(wrist_x - direction * 0.021, 0.231, -0.022),
        "ring_tip": _point(wrist_x - direction * 0.022, 0.208, -0.023),
        "pinky_mcp": _point(wrist_x - direction * 0.035, 0.305, -0.017),
        "pinky_pip": _point(wrist_x - direction * 0.039, 0.275, -0.019),
        "pinky_dip": _point(wrist_x - direction * 0.041, 0.253, -0.020),
        "pinky_tip": _point(wrist_x - direction * 0.043, 0.233, -0.021),
    }
    return tuple(coordinates[name] for name in HAND_LANDMARK_NAMES)


def _face() -> tuple[Point, ...]:
    coordinates = {
        "nose_tip": _point(0.500, 0.245, -0.035),
        "chin": _point(0.500, 0.337, -0.010),
        "left_brow_outer": _point(0.458, 0.214, -0.020),
        "left_brow_mid": _point(0.474, 0.207, -0.024),
        "left_brow_inner": _point(0.489, 0.211, -0.028),
        "right_brow_inner": _point(0.511, 0.211, -0.028),
        "right_brow_mid": _point(0.526, 0.207, -0.024),
        "right_brow_outer": _point(0.542, 0.214, -0.020),
        "left_eye_upper": _point(0.474, 0.226, -0.026),
        "left_eye_lower": _point(0.474, 0.234, -0.026),
        "right_eye_upper": _point(0.526, 0.226, -0.026),
        "right_eye_lower": _point(0.526, 0.234, -0.026),
        "mouth_left": _point(0.474, 0.286, -0.020),
        "upper_lip": _point(0.500, 0.279, -0.025),
        "lower_lip": _point(0.500, 0.296, -0.023),
        "mouth_right": _point(0.526, 0.286, -0.020),
    }
    return tuple(coordinates[name] for name in FACE_LANDMARK_NAMES)


def _frame(seq: int, capture_ms: int, *, hand_offset: float) -> LandmarkFrame:
    return LandmarkFrame(
        seq=seq,
        capture_ms=capture_ms,
        subject_id="signer-a",
        pose=_pose(hand_offset),
        left_hand=_hand(0.39 + hand_offset, direction=-1.0),
        right_hand=_hand(0.61 - hand_offset, direction=1.0),
        face=_face(),
        left_hand_score=0.97,
        right_hand_score=0.96,
        tracking_confidence=0.95,
    )


def _batch(session_id: str) -> dict[str, Any]:
    batch = LandmarkBatch(
        session_id=UUID(session_id),
        batch_seq=0,
        camera=CameraGeometry(
            source_width=1280,
            source_height=720,
            rotation_degrees=0,
            mirrored_input=True,
            coordinates_canonical=True,
        ),
        frames=(
            _frame(100, 1_000, hand_offset=0.000),
            _frame(101, 1_100, hand_offset=0.018),
        ),
        dropped_before=1,
    )
    return batch.model_dump(mode="json")


def _authorization(session: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['stream_token']}"}


def test_health_and_unconfigured_readiness_are_honest(client: TestClient) -> None:
    health = client.get("/healthz")
    readiness = client.get("/readyz")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert readiness.status_code == 503
    assert readiness.json()["status"] == "recognizer_unconfigured"
    assert readiness.json()["recognizer"]["ready"] is False
    assert readiness.json()["recognizer"]["calibrated"] is False


def test_session_creation_and_authenticated_deletion(client: TestClient) -> None:
    session = _create_session(client)
    path = f"/v1/sessions/{session['session_id']}"

    assert client.delete(path).status_code == 401
    assert client.delete(path, headers={"Authorization": "Bearer wrong-token"}).status_code == 401
    assert client.delete(path, headers=_authorization(session)).status_code == 204
    assert client.delete(path, headers=_authorization(session)).status_code == 404


def test_websocket_requires_the_session_bearer_token(client: TestClient) -> None:
    session = _create_session(client)

    with (
        pytest.raises(WebSocketDisconnect) as captured,
        client.websocket_connect(session["websocket_path"]),
    ):
        pass

    assert captured.value.code == 4401


def test_websocket_ping_round_trip(client: TestClient) -> None:
    session = _create_session(client)
    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        initial = socket.receive_json()
        assert initial["type"] == "activity"
        assert initial["state"] == "idle"

        socket.send_json(
            StreamControlMessage(
                session_id=UUID(session["session_id"]),
                control_seq=0,
                action=ControlAction.PING,
                client_ms=900,
            ).model_dump(mode="json")
        )
        pong = socket.receive_json()

    assert pong["type"] == "pong"
    assert pong["control_seq"] == 0
    assert pong["server_ms"] >= 0


def test_landmark_batch_acknowledges_received_and_dropped_frames(client: TestClient) -> None:
    session = _create_session(client)
    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(_batch(session["session_id"]))
        acknowledgement = socket.receive_json()

    assert acknowledgement["type"] == "ack"
    assert acknowledgement["batch_seq"] == 0
    assert acknowledgement["last_frame_seq"] == 101
    assert acknowledgement["received_frames"] == 2
    assert acknowledgement["buffered_frames"] == 2
    assert acknowledgement["dropped_frames"] == 1


def test_manual_commit_without_a_model_returns_repair_not_caption(client: TestClient) -> None:
    session = _create_session(client)
    session_id = UUID(session["session_id"])
    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(_batch(session["session_id"]))
        assert socket.receive_json()["type"] == "ack"

        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=0,
                action=ControlAction.COMMIT,
            ).model_dump(mode="json")
        )
        processing = socket.receive_json()
        repair = socket.receive_json()
        idle = socket.receive_json()

    assert processing["type"] == "activity"
    assert processing["state"] == "processing"
    assert repair["type"] == "repair_required"
    assert repair["status"] == "uncertain"
    assert repair["action"] == "model_unavailable"
    assert repair["confidence"] == 0.0
    assert repair["choices"] == []
    assert "recognizer_unconfigured" in repair["reason_codes"]
    assert "caption" not in repair
    assert idle["type"] == "activity"
    assert idle["state"] == "idle"


def test_malformed_websocket_input_gets_typed_retryable_error(client: TestClient) -> None:
    session = _create_session(client)
    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_text('{"type":"landmark_batch","unexpected":true}')
        error = socket.receive_json()

    assert error == {
        "type": "error",
        "code": "invalid_message",
        "message": "Message does not match the negotiated schema.",
        "retryable": True,
        "batch_seq": None,
    }


def test_drop_markers_are_scoped_to_the_committed_frame_window() -> None:
    frames = (
        _frame(100, 1_000, hand_offset=0.000),
        _frame(101, 1_100, hand_offset=0.018),
    )

    assert _client_drops_for_frames(((20, 90), (100, 2), (101, 3), (200, 7)), frames) == 5


def test_retryable_stale_end_does_not_consume_pending_sign(client: TestClient) -> None:
    session = _create_session(client)
    session_id = UUID(session["session_id"])
    with client.websocket_connect(
        session["websocket_path"], headers=_authorization(session)
    ) as socket:
        assert socket.receive_json()["state"] == "idle"
        socket.send_json(_batch(session["session_id"]))
        assert socket.receive_json()["type"] == "ack"

        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=1,
                action=ControlAction.PING,
            ).model_dump(mode="json")
        )
        assert socket.receive_json()["type"] == "pong"

        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=0,
                action=ControlAction.END,
            ).model_dump(mode="json")
        )
        stale_error = socket.receive_json()
        assert stale_error["type"] == "error"
        assert stale_error["code"] == "non_monotonic_sequence"
        assert stale_error["retryable"] is True

        socket.send_json(
            StreamControlMessage(
                session_id=session_id,
                control_seq=2,
                action=ControlAction.END,
            ).model_dump(mode="json")
        )
        assert socket.receive_json()["state"] == "processing"
        repair = socket.receive_json()
        assert repair["type"] == "repair_required"
        assert repair["action"] == "model_unavailable"
        with pytest.raises(WebSocketDisconnect) as closed:
            socket.receive_json()

    assert closed.value.code == 1000
