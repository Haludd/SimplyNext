"""Session negotiation and stream-control contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .common import ContractModel, SignLanguage
from .gloss_lattice import (
    GLOSS_LATTICE_SCHEMA_VERSION,
    MAX_GLOSS_CANDIDATES,
    MAX_GLOSS_LATTICE_BYTES,
    MAX_GLOSS_LATTICE_SLOTS,
    GlossLatticeProducer,
)
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


class StreamKind(StrEnum):
    """Explicitly negotiated frontend/backend perception boundary."""

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
    """Strict request for one explicitly selected ephemeral stream."""

    language: SignLanguage
    schema_version: Literal["1.0"] = LANDMARK_SCHEMA_VERSION
    stream_kind: StreamKind
    client: ClientDescriptor
    detector: DetectorDescriptor
    producer: GlossLatticeProducer | None = None

    @model_validator(mode="after")
    def validate_stream_profile(self) -> SessionCreateRequest:
        if self.stream_kind is StreamKind.GLOSS_LATTICE and self.producer is None:
            raise ValueError("gloss_lattice sessions require producer metadata")
        if self.stream_kind is StreamKind.LANDMARKS and self.producer is not None:
            raise ValueError("landmark sessions cannot negotiate a lattice producer")
        return self


class SessionCreateResponse(ContractModel):
    """Credentials and limits for exactly the negotiated stream kind."""

    session_id: UUID
    stream_token: str = Field(min_length=32, max_length=256)
    token_type: Literal["Bearer"] = "Bearer"
    stream_kind: StreamKind
    websocket_path: str = Field(pattern=r"^/.*")
    created_at: AwareDatetime
    expires_at: AwareDatetime
    layout: LandmarkLayout | None = None
    max_batch_frames: int | None = Field(default=None, ge=1, le=32)
    target_fps: int | None = Field(default=None, ge=1, le=60)
    lattice_schema_version: Literal["1.0"] | None = None
    max_lattice_message_bytes: Literal[32_768] | None = None
    max_lattice_slots: Literal[64] | None = None
    max_candidates_per_slot: Literal[5] | None = None

    @model_validator(mode="after")
    def validate_negotiated_limits(self) -> SessionCreateResponse:
        landmark_values = (self.layout, self.max_batch_frames, self.target_fps)
        lattice_values = (
            self.lattice_schema_version,
            self.max_lattice_message_bytes,
            self.max_lattice_slots,
            self.max_candidates_per_slot,
        )
        if self.stream_kind is StreamKind.LANDMARKS:
            if any(value is None for value in landmark_values) or any(
                value is not None for value in lattice_values
            ):
                raise ValueError("landmark response must contain only landmark limits")
        elif any(value is not None for value in landmark_values) or lattice_values != (
            GLOSS_LATTICE_SCHEMA_VERSION,
            MAX_GLOSS_LATTICE_BYTES,
            MAX_GLOSS_LATTICE_SLOTS,
            MAX_GLOSS_CANDIDATES,
        ):
            raise ValueError("lattice response must contain exactly the frozen v1 limits")
        return self


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
    control_seq: int = Field(strict=True, ge=0)
    action: ControlAction
    client_ms: int | None = Field(default=None, strict=True, ge=0)


# Backwards-friendly name for API modules that prefer the shorter term.
SessionRequest = SessionCreateRequest
SessionResponse = SessionCreateResponse
