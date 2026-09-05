"""Caption assembly contracts and the default exact-template implementation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from simplynext.recognition import RecognitionCandidate


class AssemblyStatus(StrEnum):
    CONFIDENT = "confident"
    REPAIR_REQUIRED = "repair_required"


@dataclass(frozen=True, slots=True)
class GlossEvidence:
    """The compact, accepted classifier evidence available to an assembler."""

    evidence_id: str
    gloss: str
    confidence: float
    source: str = "classifier"

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if not self.gloss.strip():
            raise ValueError("gloss must not be empty")
        if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.source.strip():
            raise ValueError("source must not be empty")

    @classmethod
    def from_candidate(
        cls,
        evidence_id: str,
        candidate: RecognitionCandidate,
    ) -> GlossEvidence:
        return cls(
            evidence_id=evidence_id,
            gloss=candidate.gloss,
            confidence=candidate.confidence,
        )


@dataclass(frozen=True, slots=True)
class AssemblyRequest:
    """An utterance payload that intentionally cannot carry camera features."""

    utterance_id: str
    language: str
    evidence: tuple[GlossEvidence, ...]

    def __post_init__(self) -> None:
        if not self.utterance_id.strip():
            raise ValueError("utterance_id must not be empty")
        if not self.language.strip():
            raise ValueError("language must not be empty")
        ids = tuple(item.evidence_id for item in self.evidence)
        if len(ids) != len(set(ids)):
            raise ValueError("evidence ids must be unique within an utterance")

    @property
    def glosses(self) -> tuple[str, ...]:
        return tuple(item.gloss for item in self.evidence)


@dataclass(frozen=True, slots=True)
class CaptionTemplate:
    caption: str
    tts_text: str | None = None

    def __post_init__(self) -> None:
        if not self.caption.strip():
            raise ValueError("caption template must not be empty")
        if self.tts_text is not None and not self.tts_text.strip():
            raise ValueError("tts_text must be omitted or non-empty")


@dataclass(frozen=True, slots=True)
class AssemblyResult:
    """A caption or an explicit refusal; never an unlabelled best effort."""

    utterance_id: str
    status: AssemblyStatus
    caption: str | None
    tts_text: str | None
    gloss_trace: tuple[GlossEvidence, ...]
    confidence: float
    source: str
    repair_action: str | None = None
    reason_codes: tuple[str, ...] = ()
    revision_count: int = 0

    @property
    def is_confident(self) -> bool:
        return self.status is AssemblyStatus.CONFIDENT


@runtime_checkable
class CaptionAssembler(Protocol):
    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        """Assemble accepted gloss evidence or return a repair result."""

        ...


class DeterministicTemplateAssembler:
    """Default assembler that emits only exact, explicitly configured sequences."""

    def __init__(
        self,
        templates: Mapping[tuple[str, ...], CaptionTemplate | str] | None = None,
    ) -> None:
        configured: dict[tuple[str, ...], CaptionTemplate] = {}
        for raw_key, raw_value in (templates or {}).items():
            key = tuple(_canonical_gloss(gloss) for gloss in raw_key)
            if not key:
                raise ValueError("caption template keys must not be empty")
            if key in configured:
                raise ValueError(f"duplicate caption template for {key!r}")
            configured[key] = (
                raw_value if isinstance(raw_value, CaptionTemplate) else CaptionTemplate(raw_value)
            )
        self._templates = configured

    @property
    def ready(self) -> bool:
        return bool(self._templates)

    @property
    def template_count(self) -> int:
        return len(self._templates)

    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        key = tuple(_canonical_gloss(gloss) for gloss in request.glosses)
        template = self._templates.get(key)
        if template is None:
            reason = "no_gloss_evidence" if not key else "exact_caption_template_not_configured"
            return repair_result(
                request,
                source="exact_template",
                reason_codes=(reason,),
                repair_action="fingerspell" if key else "repeat",
            )

        return AssemblyResult(
            utterance_id=request.utterance_id,
            status=AssemblyStatus.CONFIDENT,
            caption=template.caption,
            tts_text=template.tts_text or template.caption,
            gloss_trace=request.evidence,
            confidence=_minimum_confidence(request),
            source="exact_template",
        )


def repair_result(
    request: AssemblyRequest,
    *,
    source: str,
    reason_codes: tuple[str, ...],
    repair_action: str = "repeat",
    revision_count: int = 0,
) -> AssemblyResult:
    return AssemblyResult(
        utterance_id=request.utterance_id,
        status=AssemblyStatus.REPAIR_REQUIRED,
        caption=None,
        tts_text=None,
        gloss_trace=request.evidence,
        confidence=_minimum_confidence(request),
        source=source,
        repair_action=repair_action,
        reason_codes=reason_codes,
        revision_count=revision_count,
    )


def _minimum_confidence(request: AssemblyRequest) -> float:
    return min((item.confidence for item in request.evidence), default=0.0)


def _canonical_gloss(gloss: str) -> str:
    return gloss.strip().upper().replace(" ", "_")
