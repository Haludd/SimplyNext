"""Server-to-client WebSocket event contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, model_validator

from .common import Confidence, ContractModel, Identifier
from .utterances import GlossHypothesis, RepairAction


class ActivityState(StrEnum):
    IDLE = "idle"
    SIGNING = "signing"
    PROCESSING = "processing"


class ErrorCode(StrEnum):
    INVALID_MESSAGE = "invalid_message"
    UNAUTHORIZED = "unauthorized"
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_EXPIRED = "session_expired"
    INVALID_SESSION_STATE = "invalid_session_state"
    NON_MONOTONIC_SEQUENCE = "non_monotonic_sequence"
    BATCH_TOO_LARGE = "batch_too_large"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"


class AckEvent(ContractModel):
    type: Literal["ack"] = "ack"
    batch_seq: int = Field(ge=0)
    last_frame_seq: int = Field(ge=0)
    received_frames: int = Field(ge=0)
    buffered_frames: int = Field(ge=0)
    dropped_frames: int = Field(default=0, ge=0)
    server_ms: int = Field(ge=0)


class ActivityEvent(ContractModel):
    type: Literal["activity"] = "activity"
    state: ActivityState
    score: Confidence | None = None
    utterance_id: Identifier | None = None
    capture_ms: int | None = Field(default=None, ge=0)


class PongEvent(ContractModel):
    type: Literal["pong"] = "pong"
    control_seq: int = Field(ge=0)
    server_ms: int = Field(ge=0)


class ErrorEvent(ContractModel):
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str = Field(min_length=1, max_length=500)
    retryable: bool = False
    batch_seq: int | None = Field(default=None, ge=0)


class UtteranceResultEvent(ContractModel):
    type: Literal["utterance_result"] = "utterance_result"
    utterance_id: Identifier
    status: Literal["confident"] = "confident"
    caption: str = Field(min_length=1, max_length=500)
    tts_text: str | None = Field(default=None, min_length=1, max_length=500)
    confidence: Confidence
    gloss_trace: tuple[str, ...]
    hypotheses: tuple[GlossHypothesis, ...] = ()
    model_version: str = Field(min_length=1, max_length=128)
    latency_ms: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_latency(self) -> UtteranceResultEvent:
        if any(value < 0 for value in self.latency_ms.values()):
            raise ValueError("latency_ms values must be non-negative")
        return self


class RepairRequiredEvent(ContractModel):
    type: Literal["repair_required"] = "repair_required"
    utterance_id: Identifier
    status: Literal["uncertain"] = "uncertain"
    action: RepairAction
    message: str = Field(min_length=1, max_length=500)
    confidence: Confidence
    choices: tuple[GlossHypothesis, ...] = ()
    reason_codes: tuple[str, ...] = ()
    model_version: str | None = Field(default=None, min_length=1, max_length=128)
    latency_ms: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def choices_required_when_requested(self) -> RepairRequiredEvent:
        if self.action is RepairAction.CHOOSE_CANDIDATE and not self.choices:
            raise ValueError("choose_candidate requires choices")
        if any(value < 0 for value in self.latency_ms.values()):
            raise ValueError("latency_ms values must be non-negative")
        return self


OutboundEvent: TypeAlias = Annotated[
    AckEvent | ActivityEvent | PongEvent | ErrorEvent | UtteranceResultEvent | RepairRequiredEvent,
    Field(discriminator="type"),
]
