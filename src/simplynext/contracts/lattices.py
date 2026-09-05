"""Compact classifier-to-agent GlossLattice wire contract.

This boundary defines only symbolic classifier output and small aggregate quality
metadata. It has no raw-media, landmark-array, coordinate, or feature-tensor field;
client-supplied symbolic values still require a trusted frontend or vocabulary policy.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator, model_validator

from .common import Confidence, ContractModel, Identifier, SignLanguage

GLOSS_LATTICE_SCHEMA_VERSION: Literal["1.0"] = "1.0"
MAX_GLOSS_LATTICE_BYTES = 65_536
MAX_GLOSS_LATTICE_SLOTS = 32
MAX_GLOSS_CANDIDATES_PER_SLOT = 5
MAX_SLOT_REASON_CODES = 8
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

ReasonCode = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9_.:-]*$",
    ),
]


class GlossProvenance(StrEnum):
    """The four forward provenance rungs required by PLN T4.4."""

    CLASSIFIER_HIGH_CONFIDENCE = "classifier_high_confidence"
    TOP_K_SIGNER_CONFIRMED = "top_k_signer_confirmed"
    FINGERSPELLED = "fingerspelled"
    UNRESOLVED = "unresolved"


class ClassifierDescriptor(ContractModel):
    """Versioned classifier and calibration identity negotiated for a session."""

    name: Identifier
    model_version: Identifier
    calibration_version: Identifier
    vocabulary_version: Identifier


class GlossLatticeProducer(ContractModel):
    """Auditable frontend components that produced a lattice."""

    classifier: ClassifierDescriptor
    segmenter_version: Identifier
    top_k: int = Field(ge=1, le=MAX_GLOSS_CANDIDATES_PER_SLOT)


class GlossLatticeQuality(ContractModel):
    """Optional aggregate quality evidence; never per-point camera data."""

    observed_frames: int = Field(ge=1, le=100_000)
    dropped_frames: int = Field(default=0, ge=0, le=100_000)
    landmark_coverage: Confidence
    classifier_latency_ms: int = Field(ge=0, le=60_000)

    @property
    def dropped_fraction(self) -> float:
        attempted = self.observed_frames + self.dropped_frames
        return self.dropped_frames / attempted if attempted else 0.0


class GlossCandidate(ContractModel):
    """One ranked, calibrated classifier hypothesis for a slot."""

    rank: int = Field(ge=1, le=MAX_GLOSS_CANDIDATES_PER_SLOT)
    gloss: str = Field(min_length=1, max_length=128)
    confidence: Confidence

    @field_validator("gloss")
    @classmethod
    def reject_blank_gloss(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("gloss must not be blank")
        return value


class GlossLatticeSlot(ContractModel):
    """One temporal gloss slot with explicit resolution and provenance."""

    slot_id: Identifier
    start_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    end_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    candidates: Annotated[
        tuple[GlossCandidate, ...],
        Field(max_length=MAX_GLOSS_CANDIDATES_PER_SLOT),
    ]
    resolved_gloss: str | None = Field(default=None, min_length=1, max_length=128)
    selected_rank: int | None = Field(
        default=None,
        ge=1,
        le=MAX_GLOSS_CANDIDATES_PER_SLOT,
    )
    provenance: GlossProvenance
    confirmed_at_ms: int | None = Field(default=None, ge=0, le=MAX_SAFE_JSON_INTEGER)
    reason_codes: Annotated[
        tuple[ReasonCode, ...],
        Field(max_length=MAX_SLOT_REASON_CODES),
    ] = ()

    @model_validator(mode="after")
    def validate_slot(self) -> GlossLatticeSlot:
        if self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be greater than start_ms")

        expected_ranks = tuple(range(1, len(self.candidates) + 1))
        actual_ranks = tuple(candidate.rank for candidate in self.candidates)
        if actual_ranks != expected_ranks:
            raise ValueError("candidate ranks must be contiguous and start at 1")
        confidences = tuple(candidate.confidence for candidate in self.candidates)
        if any(left < right for left, right in zip(confidences, confidences[1:], strict=False)):
            raise ValueError("candidates must be ordered by non-increasing confidence")
        canonical_glosses = tuple(_canonical_gloss(item.gloss) for item in self.candidates)
        if len(canonical_glosses) != len(set(canonical_glosses)):
            raise ValueError("candidate glosses must be unique within a slot")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("reason_codes must be unique within a slot")

        selected = self._selected_candidate()
        if self.provenance is GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE:
            if selected is None or selected.rank != 1:
                raise ValueError("classifier_high_confidence must select rank 1")
            if self.confirmed_at_ms is not None:
                raise ValueError("classifier_high_confidence cannot have confirmed_at_ms")
            self._require_resolved_match(selected)
        elif self.provenance is GlossProvenance.TOP_K_SIGNER_CONFIRMED:
            if selected is None:
                raise ValueError("top_k_signer_confirmed requires a selected candidate")
            if self.confirmed_at_ms is None:
                raise ValueError("top_k_signer_confirmed requires confirmed_at_ms")
            self._require_resolved_match(selected)
        elif self.provenance is GlossProvenance.FINGERSPELLED:
            if self.resolved_gloss is None:
                raise ValueError("fingerspelled requires resolved_gloss")
            if self.selected_rank is not None:
                raise ValueError("fingerspelled cannot select a classifier rank")
            if self.confirmed_at_ms is None:
                raise ValueError("fingerspelled requires confirmed_at_ms")
        else:
            if self.resolved_gloss is not None or self.selected_rank is not None:
                raise ValueError("unresolved slots cannot contain a resolution")
            if self.confirmed_at_ms is not None:
                raise ValueError("unresolved slots cannot have confirmed_at_ms")
            if not self.reason_codes:
                raise ValueError("unresolved slots require at least one reason_code")
        return self

    def _selected_candidate(self) -> GlossCandidate | None:
        if self.selected_rank is None:
            return None
        if self.selected_rank > len(self.candidates):
            raise ValueError("selected_rank does not identify a candidate")
        return self.candidates[self.selected_rank - 1]

    def _require_resolved_match(self, candidate: GlossCandidate) -> None:
        if self.resolved_gloss != candidate.gloss:
            raise ValueError("resolved_gloss must equal the selected candidate gloss")

    @property
    def selected_candidate(self) -> GlossCandidate | None:
        """Return the selected classifier candidate, if this slot uses one."""

        return self._selected_candidate()


class GlossLattice(ContractModel):
    """One compact, revisioned utterance lattice sent to the Agent boundary."""

    type: Literal["gloss_lattice"] = "gloss_lattice"
    schema_version: Literal["1.0"] = GLOSS_LATTICE_SCHEMA_VERSION
    session_id: UUID
    lattice_seq: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    utterance_id: Identifier
    revision: int = Field(default=0, ge=0, le=32)
    language: SignLanguage
    subject_id: Identifier
    is_final: bool
    capture_start_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    capture_end_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    produced_ms: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    producer: GlossLatticeProducer
    quality: GlossLatticeQuality | None = None
    slots: Annotated[
        tuple[GlossLatticeSlot, ...],
        Field(min_length=1, max_length=MAX_GLOSS_LATTICE_SLOTS),
    ]

    @model_validator(mode="after")
    def validate_lattice(self) -> GlossLattice:
        if self.capture_end_ms <= self.capture_start_ms:
            raise ValueError("capture_end_ms must be greater than capture_start_ms")
        if self.produced_ms < self.capture_end_ms:
            raise ValueError("produced_ms must not precede capture_end_ms")

        slot_ids = tuple(slot.slot_id for slot in self.slots)
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("slot_id values must be unique within a lattice")

        previous_start = -1
        for slot in self.slots:
            if slot.start_ms < self.capture_start_ms or slot.end_ms > self.capture_end_ms:
                raise ValueError("slot timestamps must lie inside the capture interval")
            if slot.start_ms < previous_start:
                raise ValueError("slots must be ordered by start_ms")
            if len(slot.candidates) > self.producer.top_k:
                raise ValueError("slot candidate count exceeds producer.top_k")
            if slot.confirmed_at_ms is not None and not (
                self.capture_start_ms <= slot.confirmed_at_ms <= self.produced_ms
            ):
                raise ValueError("confirmed_at_ms must lie between capture start and production")
            previous_start = slot.start_ms
        return self


def _canonical_gloss(value: str) -> str:
    return value.strip().upper().replace(" ", "_")
