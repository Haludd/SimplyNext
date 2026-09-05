"""The existing ``POST /v1/utterances`` compatibility seam."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, Field, JsonValue, field_validator, model_validator

from .common import Confidence, ContractModel, Identifier, SignLanguage


class TranslationStatus(StrEnum):
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    ERROR = "error"


class RepairAction(StrEnum):
    REPEAT = "repeat"
    FINGERSPELL = "fingerspell"
    CHOOSE_CANDIDATE = "choose_candidate"
    REPOSITION = "reposition"
    RECONNECT = "reconnect"
    MODEL_UNAVAILABLE = "model_unavailable"
    ESCALATE = "escalate"


class GlossHypothesis(ContractModel):
    gloss: str = Field(min_length=1, max_length=128)
    confidence: Confidence

    @field_validator("gloss")
    @classmethod
    def reject_blank_gloss(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gloss must not be blank")
        return value


class UtteranceRequest(ContractModel):
    session_id: Identifier
    utterance_id: Identifier
    language: SignLanguage
    started_at: AwareDatetime
    ended_at: AwareDatetime
    hypotheses: Annotated[
        tuple[GlossHypothesis, ...],
        Field(min_length=1, max_length=10),
    ]
    features: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_range(self) -> UtteranceRequest:
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be later than started_at")
        if len(self.features) > 64:
            raise ValueError("features must contain at most 64 entries")
        return self


class TranslationResult(ContractModel):
    utterance_id: Identifier
    status: TranslationStatus
    caption: str | None = Field(default=None, min_length=1, max_length=500)
    tts_text: str | None = Field(default=None, min_length=1, max_length=500)
    gloss_trace: tuple[str, ...] = ()
    confidence: Confidence
    repair_action: RepairAction | None = None
    message: str | None = Field(default=None, min_length=1, max_length=500)
    choices: tuple[GlossHypothesis, ...] = ()
    reason_codes: tuple[str, ...] = ()
    model_version: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def enforce_no_guessing_policy(self) -> TranslationResult:
        if self.status is TranslationStatus.CONFIDENT:
            if self.caption is None:
                raise ValueError("a confident result requires caption")
            if self.repair_action is not None:
                raise ValueError("a confident result cannot request repair")
        else:
            if self.caption is not None or self.tts_text is not None:
                raise ValueError("a non-confident result cannot emit caption or TTS text")
        if self.repair_action is RepairAction.CHOOSE_CANDIDATE and not self.choices:
            raise ValueError("choose_candidate requires choices")
        return self


# Names used by the checked-in Flutter API client.
UtterancePayload = UtteranceRequest
UtteranceResponse = TranslationResult
