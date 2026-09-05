"""Authoritative CTR version 1.0 classifier-to-Agent GlossLattice contract.

The wire shape in this module mirrors ``CTR_contracts.md`` exactly. It contains
only compact symbolic classifier output: no camera media, landmarks, feature
arrays, signer identity, Agent state, or repair-loop state.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from .common import Confidence, ContractModel, Identifier, SignLanguage

GLOSS_LATTICE_SCHEMA_VERSION: Literal["1.0"] = "1.0"
GLOSS_LATTICE_TIMEBASE: Literal["session_monotonic_ms"] = "session_monotonic_ms"
GLOSS_LATTICE_CONFIDENCE_KIND: Literal["calibrated_probability"] = "calibrated_probability"
MAX_GLOSS_LATTICE_BYTES: Literal[32_768] = 32_768
MAX_GLOSS_LATTICE_SLOTS: Literal[64] = 64
MAX_GLOSS_CANDIDATES_PER_SLOT: Literal[5] = 5
MAX_SAFE_JSON_INTEGER: Literal[9_007_199_254_740_991] = 9_007_199_254_740_991


class _GlossLatticeContractModel(ContractModel):
    """CTR-local strict model behavior without changing legacy API contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
        validate_default=True,
    )


class GlossProvenance(StrEnum):
    """How a slot's resolved gloss was established."""

    CLASSIFIER_HIGH_CONFIDENCE = "classifier_high_confidence"
    TOP_K_SIGNER_CONFIRMED = "top_k_signer_confirmed"
    FINGERSPELLED = "fingerspelled"
    UNRESOLVED = "unresolved"


class GlossLatticeProducer(_GlossLatticeContractModel):
    """Versioned classifier, calibration, and vocabulary lineage."""

    classifier_id: Identifier
    classifier_version: Identifier
    confidence_kind: Literal["calibrated_probability"]
    calibration_version: Identifier
    vocabulary_version: Identifier


class GlossCandidate(_GlossLatticeContractModel):
    """One ranked calibrated closed-vocabulary hypothesis."""

    gloss_id: Identifier
    rank: int = Field(ge=1, le=MAX_GLOSS_CANDIDATES_PER_SLOT)
    confidence: Confidence


class GlossSlot(_GlossLatticeContractModel):
    """One non-overlapping temporal slot in the ordered lattice."""

    slot_index: int = Field(ge=0, le=MAX_GLOSS_LATTICE_SLOTS - 1)
    slot_id: Identifier
    start_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    end_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    candidates: Annotated[
        tuple[GlossCandidate, ...],
        Field(max_length=MAX_GLOSS_CANDIDATES_PER_SLOT),
    ]
    resolved_gloss_id: Identifier | None
    provenance: GlossProvenance

    @model_validator(mode="after")
    def validate_slot(self) -> GlossSlot:
        if self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be greater than start_ms")

        expected_ranks = tuple(range(1, len(self.candidates) + 1))
        actual_ranks = tuple(candidate.rank for candidate in self.candidates)
        if actual_ranks != expected_ranks:
            raise ValueError("candidate ranks must be contiguous and start at 1")

        confidences = tuple(candidate.confidence for candidate in self.candidates)
        if any(left < right for left, right in zip(confidences, confidences[1:], strict=False)):
            raise ValueError("candidates must be ordered by non-increasing confidence")

        gloss_ids = tuple(candidate.gloss_id for candidate in self.candidates)
        if len(gloss_ids) != len(set(gloss_ids)):
            raise ValueError("candidate gloss_id values must be unique within a slot")

        if self.provenance is GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE:
            if not self.candidates:
                raise ValueError("classifier_high_confidence requires at least one candidate")
            if self.resolved_gloss_id != self.candidates[0].gloss_id:
                raise ValueError(
                    "classifier_high_confidence resolved_gloss_id must equal the rank-1 gloss_id"
                )
        elif self.provenance is GlossProvenance.TOP_K_SIGNER_CONFIRMED:
            if self.resolved_gloss_id is None:
                raise ValueError("top_k_signer_confirmed requires resolved_gloss_id")
            if self.resolved_gloss_id not in gloss_ids:
                raise ValueError(
                    "top_k_signer_confirmed resolved_gloss_id must identify a retained candidate"
                )
        elif self.provenance is GlossProvenance.FINGERSPELLED:
            if self.resolved_gloss_id is None:
                raise ValueError("fingerspelled requires resolved_gloss_id")
        elif self.resolved_gloss_id is not None:
            raise ValueError("unresolved slots cannot contain resolved_gloss_id")
        return self

    @property
    def resolved_candidate(self) -> GlossCandidate | None:
        """Return the candidate matching ``resolved_gloss_id``, if retained."""

        if self.resolved_gloss_id is None:
            return None
        return next(
            (
                candidate
                for candidate in self.candidates
                if candidate.gloss_id == self.resolved_gloss_id
            ),
            None,
        )


class GlossLattice(_GlossLatticeContractModel):
    """One exact CTR v1 lattice transported as a UTF-8 JSON object."""

    type: Literal["gloss_lattice"]
    schema_version: Literal["1.0"]
    session_id: UUID
    lattice_seq: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    utterance_id: Identifier
    language: SignLanguage
    timebase: Literal["session_monotonic_ms"]
    started_at_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    ended_at_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    producer: GlossLatticeProducer
    slots: Annotated[
        tuple[GlossSlot, ...],
        Field(min_length=1, max_length=MAX_GLOSS_LATTICE_SLOTS),
    ]

    @model_validator(mode="after")
    def validate_lattice(self) -> GlossLattice:
        if self.ended_at_ms <= self.started_at_ms:
            raise ValueError("ended_at_ms must be greater than started_at_ms")

        slot_ids = tuple(slot.slot_id for slot in self.slots)
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("slot_id values must be unique within a lattice")

        previous_end_ms: int | None = None
        for expected_index, slot in enumerate(self.slots):
            if slot.slot_index != expected_index:
                raise ValueError("slot_index values must be contiguous and match array order")
            if slot.start_ms < self.started_at_ms or slot.end_ms > self.ended_at_ms:
                raise ValueError("slot timestamps must lie inside the utterance interval")
            if previous_end_ms is not None and slot.start_ms < previous_end_ms:
                raise ValueError("slot intervals must not overlap")
            previous_end_ms = slot.end_ms
        return self
