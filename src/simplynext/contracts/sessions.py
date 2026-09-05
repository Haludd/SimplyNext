"""Session negotiation and stream-control contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from .common import ContractModel, SignLanguage
from .landmarks import LANDMARK_SCHEMA_VERSION, LandmarkLayout


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


class ClientDescriptor(ContractModel):
    platform: ClientPlatform
    app_version: str = Field(min_length=1, max_length=64)
    device_model: str | None = Field(default=None, min_length=1, max_length=128)


class DetectorDescriptor(ContractModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    delegate: DetectorDelegate = DetectorDelegate.UNKNOWN


class SessionCreateRequest(ContractModel):
    """Strict request for a new ephemeral landmark-streaming session."""

    language: SignLanguage
    schema_version: Literal["1.0"] = LANDMARK_SCHEMA_VERSION
    client: ClientDescriptor
    detector: DetectorDescriptor


class SessionCreateResponse(ContractModel):
    """Credentials and negotiated layout for one ephemeral session."""

    session_id: UUID
    stream_token: str = Field(min_length=32, max_length=256)
    token_type: Literal["Bearer"] = "Bearer"
    websocket_path: str = Field(pattern=r"^/.*")
    created_at: AwareDatetime
    expires_at: AwareDatetime
    layout: LandmarkLayout = Field(default_factory=LandmarkLayout)
    max_batch_frames: int = Field(ge=1, le=32)
    target_fps: int = Field(default=20, ge=1, le=60)


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
