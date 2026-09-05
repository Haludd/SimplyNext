from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from simplynext.config import Settings
from simplynext.contracts import (
    FACE_LANDMARK_INDICES,
    FACE_LANDMARK_NAMES,
    HAND_LANDMARK_NAMES,
    POSE_LANDMARK_INDICES,
    POSE_LANDMARK_NAMES,
    CameraGeometry,
    ClientDescriptor,
    ClientPlatform,
    DetectorDescriptor,
    GlossHypothesis,
    InboundStreamMessage,
    LandmarkBatch,
    LandmarkFrame,
    RepairAction,
    SessionCreateRequest,
    SignLanguage,
    StreamControlMessage,
    TranslationResult,
    TranslationStatus,
    UtteranceRequest,
)

SESSION_ID = UUID("12345678-1234-5678-1234-567812345678")


def point(confidence: float = 1.0) -> tuple[float, float, float, float]:
    return (0.25, 0.50, -0.02, confidence)


def pose() -> tuple[tuple[float, float, float, float], ...]:
    return tuple(point() for _ in POSE_LANDMARK_NAMES)


def hand() -> tuple[tuple[float, float, float, float], ...]:
    return tuple(point() for _ in HAND_LANDMARK_NAMES)


def frame(seq: int = 0, capture_ms: int = 100) -> LandmarkFrame:
    return LandmarkFrame(
        seq=seq,
        capture_ms=capture_ms,
        subject_id="signer-1",
        pose=pose(),
        left_hand=hand(),
        left_hand_score=0.95,
        tracking_confidence=0.90,
    )


def camera() -> CameraGeometry:
    return CameraGeometry(
        source_width=1280,
        source_height=720,
        rotation_degrees=0,
        mirrored_input=True,
    )


def test_layouts_are_fixed_and_match_mediapipe_indices() -> None:
    assert len(HAND_LANDMARK_NAMES) == 21
    assert len(POSE_LANDMARK_NAMES) == 9
    assert len(FACE_LANDMARK_NAMES) == 16
    assert POSE_LANDMARK_INDICES["left_shoulder"] == 11
    assert FACE_LANDMARK_INDICES["upper_lip"] == 13


def test_landmark_arrays_are_compact_and_exact_length() -> None:
    valid = frame()
    dumped = valid.model_dump(mode="json")
    assert dumped["left_hand"][0] == [0.25, 0.50, -0.02, 1.0]
    assert dumped["subject_id"] == "signer-1"

    with pytest.raises(ValidationError):
        LandmarkFrame(seq=0, capture_ms=100, left_hand=hand()[:-1])
    with pytest.raises(ValidationError):
        LandmarkFrame(
            seq=0,
            capture_ms=100,
            left_hand=hand()[:-1] + (point(1.1),),
        )
    with pytest.raises(ValidationError):
        LandmarkFrame(seq=0, capture_ms=100, left_hand_score=0.8)
    with pytest.raises(ValidationError):
        LandmarkFrame(seq=0, capture_ms=100, subject_id="")
    with pytest.raises(ValidationError):
        LandmarkFrame(
            seq=0,
            capture_ms=100,
            left_hand=((5.0, 0.5, 0.0, 1.0), *hand()[1:]),
        )


def test_batch_requires_monotonic_frames_and_canonical_coordinates() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        LandmarkBatch(
            session_id=SESSION_ID,
            batch_seq=0,
            camera=camera(),
            frames=(frame(2, 200), frame(1, 210)),
        )

    with pytest.raises(ValidationError):
        CameraGeometry(
            source_width=1280,
            source_height=720,
            rotation_degrees=0,
            mirrored_input=True,
            coordinates_canonical=False,
        )


def test_inbound_union_uses_type_discriminator() -> None:
    adapter = TypeAdapter(InboundStreamMessage)
    parsed = adapter.validate_python(
        {
            "type": "control",
            "session_id": str(SESSION_ID),
            "control_seq": 3,
            "action": "pause",
        }
    )
    assert isinstance(parsed, StreamControlMessage)


def test_session_request_is_strict_and_versioned() -> None:
    request = SessionCreateRequest(
        language=SignLanguage.SGSL,
        client=ClientDescriptor(platform=ClientPlatform.ANDROID, app_version="0.1.0"),
        detector=DetectorDescriptor(name="mediapipe-holistic", version="0.10.21"),
    )
    assert request.schema_version == "1.0"

    with pytest.raises(ValidationError, match="Extra inputs"):
        SessionCreateRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "raw_video": True,
            }
        )
    with pytest.raises(ValidationError):
        SessionCreateRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "schema_version": "2.0",
            }
        )


def test_utterance_seam_matches_flutter_and_enforces_time_order() -> None:
    started = datetime(2026, 9, 5, 8, 0, tzinfo=UTC)
    request = UtteranceRequest(
        session_id="session-123",
        utterance_id="utt-008",
        language="sgsl",
        started_at=started,
        ended_at=started + timedelta(seconds=2),
        hypotheses=(GlossHypothesis(gloss="WATER", confidence=0.96),),
        features={"hands_visible": True, "frame_count": 36},
    )
    assert request.model_dump(mode="json")["session_id"] == "session-123"

    with pytest.raises(ValidationError, match="later"):
        UtteranceRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "ended_at": started.isoformat(),
            }
        )


def test_non_confident_translation_cannot_put_words_in_signers_mouth() -> None:
    confident = TranslationResult(
        utterance_id="utt-008",
        status=TranslationStatus.CONFIDENT,
        caption="Water, please.",
        tts_text="Water, please.",
        gloss_trace=("WATER", "PLEASE"),
        confidence=0.91,
    )
    assert confident.caption == "Water, please."

    with pytest.raises(ValidationError, match="cannot emit caption"):
        TranslationResult(
            utterance_id="utt-009",
            status=TranslationStatus.UNCERTAIN,
            caption="Maybe water.",
            confidence=0.40,
            repair_action=RepairAction.REPEAT,
        )
    with pytest.raises(ValidationError, match="requires choices"):
        TranslationResult(
            utterance_id="utt-010",
            status=TranslationStatus.UNCERTAIN,
            confidence=0.55,
            repair_action=RepairAction.CHOOSE_CANDIDATE,
        )


def test_settings_use_namespaced_non_secret_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLYNEXT_PORT", "8123")
    monkeypatch.setenv("SIMPLYNEXT_SESSION_TTL_SECONDS", "120")
    monkeypatch.setenv(
        "SIMPLYNEXT_ALLOWED_ORIGINS",
        "http://localhost:3000,http://192.168.1.10:8080",
    )
    settings = Settings(_env_file=None)
    assert settings.port == 8123
    assert settings.session_ttl_seconds == 120
    assert settings.allowed_origins == (
        "http://localhost:3000",
        "http://192.168.1.10:8080",
    )
    assert "aws_access_key_id" not in Settings.model_fields
    assert "aws_secret_access_key" not in Settings.model_fields
