"""Session negotiation and stream-control contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .common import ContractModel, SignLanguage
from .landmarks import LANDMARK_SCHEMA_VERSION, LandmarkLayout
from .lattices import (
    GLOSS_LATTICE_SCHEMA_VERSION,
    MAX_GLOSS_CANDIDATES_PER_SLOT,
    MAX_GLOSS_LATTICE_BYTES,
    MAX_GLOSS_LATTICE_SLOTS,
    ClassifierDescriptor,
)


class ClientPlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"
    TEST = "test"


class DetectorDelegate(StrEnum):
    CPU = "cpu"
    GPU = "gpu"
    NNAPI = "nnapi"
    CORE_ML = "core_ml"
    UNKNOWN = "unknown"


class StreamKind(StrEnum):
    """Which frontend/backend boundary owns perception for this session."""

    LANDMARKS = "landmarks"
    GLOSS_LATTICE = "gloss_lattice"


class ClientDescriptor(ContractModel):
    platform: ClientPlatform
    app_version: str = Field(min_length=1, max_length=64)
    device_model: str | None = Field(default=None, min_length=1, max_length=128)


class DetectorDescriptor(ContractModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    delegate: DetectorDelegate = DetectorDelegate.UNKNOWN


class SessionCreateRequest(ContractModel):
    """Strict request for a new ephemeral translation session."""

    language: SignLanguage
    schema_version: Literal["1.0"] = LANDMARK_SCHEMA_VERSION
    stream_kind: StreamKind = StreamKind.LANDMARKS
    client: ClientDescriptor
    detector: DetectorDescriptor
    classifier: ClassifierDescriptor | None = None

    @model_validator(mode="after")
    def require_classifier_for_lattice_stream(self) -> SessionCreateRequest:
        if self.stream_kind is StreamKind.GLOSS_LATTICE and self.classifier is None:
            raise ValueError("gloss_lattice sessions require classifier metadata")
        return self


class SessionCreateResponse(ContractModel):
    """Credentials and negotiated layout for one ephemeral session."""

    session_id: UUID
    stream_token: str = Field(min_length=32, max_length=256)
    token_type: Literal["Bearer"] = "Bearer"
    stream_kind: StreamKind
    websocket_path: str = Field(pattern=r"^/.*")
    lattice_websocket_path: str | None = Field(default=None, pattern=r"^/.*")
    created_at: AwareDatetime
    expires_at: AwareDatetime
    layout: LandmarkLayout = Field(default_factory=LandmarkLayout)
    max_batch_frames: int = Field(ge=1, le=32)
    target_fps: int = Field(default=20, ge=1, le=60)
    lattice_schema_version: Literal["1.0"] = GLOSS_LATTICE_SCHEMA_VERSION
    max_lattice_message_bytes: int = Field(
        default=MAX_GLOSS_LATTICE_BYTES,
        ge=4_096,
        le=MAX_GLOSS_LATTICE_BYTES,
    )
    max_lattice_slots: int = Field(
        default=MAX_GLOSS_LATTICE_SLOTS,
        ge=1,
        le=MAX_GLOSS_LATTICE_SLOTS,
    )
    max_candidates_per_slot: int = Field(
        default=MAX_GLOSS_CANDIDATES_PER_SLOT,
        ge=1,
        le=MAX_GLOSS_CANDIDATES_PER_SLOT,
    )


class ControlAction(StrEnum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    COMMIT = "commit"
    END = "end"
    PING = "ping"
    CLEAR_LIVE_DATA = "clear_live_data"


class StreamControlMessage(ContractModel):
    """Ordered client control message on the session WebSocket."""

    type: Literal["control"] = "control"
    session_id: UUID
    control_seq: int = Field(ge=0)
    action: ControlAction
    client_ms: int | None = Field(default=None, ge=0)


# Backwards-friendly name for API modules that prefer the shorter term.
SessionRequest = SessionCreateRequest
SessionResponse = SessionCreateResponse
