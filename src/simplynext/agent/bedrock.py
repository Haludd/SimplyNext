"""Optional, bounded Bedrock Converse caption assembler and critic.

``boto3`` is imported only by ``create_bedrock_client``.  The main class accepts an
injected Converse-compatible client, which keeps local operation and tests offline.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final, Protocol, cast

from .assembler import (
    AssemblyRequest,
    AssemblyResult,
    AssemblyStatus,
    repair_result,
)

BEDROCK_MODEL_ID_ENV: Final[str] = "SIMPLYNEXT_BEDROCK_MODEL_ID"
BEDROCK_REGION_ENV: Final[str] = "AWS_REGION"
MAX_ALLOWED_REVISIONS: Final[int] = 1

_ASSEMBLER_SYSTEM: Final[str] = (
    "Assemble a short caption from the ordered closed-vocabulary gloss evidence. "
    "Do not add an event, object, person, intent, or certainty that is not supported by "
    "that evidence. Return only JSON with keys caption, tts_text, used_evidence_ids, "
    "and used_glosses. The two text fields must be identical."
)
_CRITIC_SYSTEM: Final[str] = (
    "Check whether the proposed caption is completely supported by the ordered gloss "
    "evidence. Fluency never outweighs evidence. Return only JSON with the keys "
    "supported and reason."
)
_REVISION_SYSTEM: Final[str] = (
    "Revise the proposed caption once, using only the ordered gloss evidence and the "
    "listed failure reason. Return only JSON with keys caption, tts_text, "
    "used_evidence_ids, and used_glosses. The two text fields must be identical."
)

logger = logging.getLogger(__name__)


class ConverseClient(Protocol):
    """The subset of the boto3 Bedrock Runtime client used by this module."""

    def converse(self, **kwargs: Any) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class BedrockAssemblerConfig:
    """Explicit configuration; the model ID is consumed verbatim, never constructed."""

    model_id: str
    max_tokens: int = 300
    temperature: float = 0.0
    max_revisions: int = MAX_ALLOWED_REVISIONS
    max_caption_characters: int = 240

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("Bedrock model_id must not be empty")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("temperature must be between 0 and 1")
        if not 0 <= self.max_revisions <= MAX_ALLOWED_REVISIONS:
            raise ValueError("max_revisions must be zero or one")
        if self.max_caption_characters < 1:
            raise ValueError("max_caption_characters must be positive")

    @classmethod
    def from_env(cls) -> BedrockAssemblerConfig:
        model_id = os.environ.get(BEDROCK_MODEL_ID_ENV, "").strip()
        if not model_id:
            raise RuntimeError(f"{BEDROCK_MODEL_ID_ENV} is not configured")
        return cls(model_id=model_id)


@dataclass(slots=True)
class _AssemblyState:
    revision_count: int = 0
    model_call_count: int = 0


@dataclass(frozen=True, slots=True)
class _Draft:
    caption: str
    tts_text: str
    used_evidence_ids: tuple[str, ...]
    used_glosses: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Critique:
    supported: bool
    reason: str


class BedrockCaptionAssembler:
    """Use Bedrock for a bounded assemble/critic workflow with deterministic checks."""

    def __init__(self, client: ConverseClient, config: BedrockAssemblerConfig) -> None:
        self._client = client
        self._config = config

    @property
    def ready(self) -> bool:
        """Report configuration readiness; calls can still fail closed at runtime."""

        return True

    def assemble(self, request: AssemblyRequest) -> AssemblyResult:
        if not request.evidence:
            return repair_result(
                request,
                source="bedrock_converse",
                reason_codes=("no_gloss_evidence",),
            )

        state = _AssemblyState()
        try:
            raw_draft = self._invoke(
                role="assembler",
                system_prompt=_ASSEMBLER_SYSTEM,
                payload={"request": _evidence_payload(request)},
                state=state,
            )
            draft, errors = _parse_and_check_draft(
                raw_draft,
                request,
                max_characters=self._config.max_caption_characters,
            )

            while True:
                # The state counter is the hard loop bound required by the agent policy.
                if errors:
                    if state.revision_count >= self._config.max_revisions:
                        return repair_result(
                            request,
                            source="bedrock_converse",
                            reason_codes=tuple(errors),
                            revision_count=state.revision_count,
                        )
                    raw_draft = self._revise(
                        request,
                        raw_draft,
                        "; ".join(errors),
                        state,
                    )
                    draft, errors = _parse_and_check_draft(
                        raw_draft,
                        request,
                        max_characters=self._config.max_caption_characters,
                    )
                    continue

                assert draft is not None
                critique = self._critic(request, draft, state)
                if critique.supported:
                    return _accepted_result(request, draft, state.revision_count)
                if state.revision_count >= self._config.max_revisions:
                    return repair_result(
                        request,
                        source="bedrock_converse",
                        reason_codes=("critic_rejected_caption",),
                        revision_count=state.revision_count,
                    )
                raw_draft = self._revise(
                    request,
                    raw_draft,
                    critique.reason or "critic rejected the caption",
                    state,
                )
                draft, errors = _parse_and_check_draft(
                    raw_draft,
                    request,
                    max_characters=self._config.max_caption_characters,
                )
        except Exception as exc:  # fail closed for optional network/model failures
            logger.warning("bedrock_caption_assembly_failed", exc_info=exc)
            return repair_result(
                request,
                source="bedrock_converse",
                reason_codes=("language_service_unavailable",),
                revision_count=state.revision_count,
            )

    def _revise(
        self,
        request: AssemblyRequest,
        previous_output: str,
        reason: str,
        state: _AssemblyState,
    ) -> str:
        if state.revision_count >= self._config.max_revisions:
            raise RuntimeError("revision bound reached")
        state.revision_count += 1
        return self._invoke(
            role="revision",
            system_prompt=_REVISION_SYSTEM,
            payload={
                "request": _evidence_payload(request),
                "previous_output": previous_output,
                "failure_reason": reason,
                "revision_number": state.revision_count,
            },
            state=state,
        )

    def _critic(
        self,
        request: AssemblyRequest,
        draft: _Draft,
        state: _AssemblyState,
    ) -> _Critique:
        raw = self._invoke(
            role="critic",
            system_prompt=_CRITIC_SYSTEM,
            payload={
                "request": _evidence_payload(request),
                "proposed_caption": _draft_payload(draft),
            },
            state=state,
        )
        return _parse_critique(raw)

    def _invoke(
        self,
        *,
        role: str,
        system_prompt: str,
        payload: Mapping[str, Any],
        state: _AssemblyState,
    ) -> str:
        state.model_call_count += 1
        response: Mapping[str, Any] | None = None
        try:
            response = self._client.converse(
                modelId=self._config.model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": json.dumps(
                                    payload,
                                    ensure_ascii=True,
                                    separators=(",", ":"),
                                )
                            }
                        ],
                    }
                ],
                inferenceConfig={
                    "maxTokens": self._config.max_tokens,
                    "temperature": self._config.temperature,
                },
            )
            return _response_text(response)
        finally:
            usage = response.get("usage", {}) if response is not None else {}
            if not isinstance(usage, Mapping):
                usage = {}
            # Prompts and evidence are intentionally not logged. Every attempted call emits
            # a usage event, including failed calls where token counts are unavailable.
            logger.info(
                "bedrock_converse_usage role=%s call=%d input_tokens=%s "
                "output_tokens=%s total_tokens=%s status=%s",
                role,
                state.model_call_count,
                usage.get("inputTokens"),
                usage.get("outputTokens"),
                usage.get("totalTokens"),
                "ok" if response is not None else "failed",
            )


def create_bedrock_client(*, region_name: str | None = None) -> ConverseClient:
    """Create the optional boto3 client without making a network request."""

    try:
        import boto3  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on optional installation
        raise RuntimeError("boto3 is required for Bedrock caption assembly") from exc
    region = region_name or os.environ.get(BEDROCK_REGION_ENV) or None
    return cast(ConverseClient, boto3.client("bedrock-runtime", region_name=region))


def _evidence_payload(request: AssemblyRequest) -> dict[str, Any]:
    """Whitelist the only request fields allowed to enter a model prompt."""

    return {
        "utterance_id": request.utterance_id,
        "language": request.language,
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "gloss": item.gloss,
                "confidence": round(item.confidence, 6),
            }
            for item in request.evidence
        ],
    }


def _draft_payload(draft: _Draft) -> dict[str, Any]:
    return {
        "caption": draft.caption,
        "tts_text": draft.tts_text,
        "used_evidence_ids": list(draft.used_evidence_ids),
        "used_glosses": list(draft.used_glosses),
    }


def _parse_and_check_draft(
    raw: str,
    request: AssemblyRequest,
    *,
    max_characters: int,
) -> tuple[_Draft | None, tuple[str, ...]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None, ("assembler_returned_invalid_json",)
    if not isinstance(value, Mapping):
        return None, ("assembler_response_is_not_an_object",)

    expected_keys = {"caption", "tts_text", "used_evidence_ids", "used_glosses"}
    if set(value) != expected_keys:
        return None, ("assembler_response_schema_mismatch",)
    caption = value.get("caption")
    tts_text = value.get("tts_text")
    ids = value.get("used_evidence_ids")
    glosses = value.get("used_glosses")
    if (
        not isinstance(caption, str)
        or not isinstance(tts_text, str)
        or not isinstance(ids, list)
        or not all(isinstance(item, str) for item in ids)
        or not isinstance(glosses, list)
        or not all(isinstance(item, str) for item in glosses)
    ):
        return None, ("assembler_response_schema_mismatch",)

    draft = _Draft(caption, tts_text, tuple(ids), tuple(glosses))
    errors: list[str] = []
    if not caption.strip() or len(caption) > max_characters:
        errors.append("caption_length_invalid")
    if caption != tts_text:
        errors.append("tts_text_must_equal_caption")
    expected_ids = tuple(item.evidence_id for item in request.evidence)
    expected_glosses = tuple(item.gloss for item in request.evidence)
    if draft.used_evidence_ids != expected_ids:
        errors.append("evidence_ids_do_not_match")
    if draft.used_glosses != expected_glosses:
        errors.append("gloss_trace_does_not_match")
    return draft, tuple(errors)


def _parse_critique(raw: str) -> _Critique:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("critic returned invalid JSON") from exc
    if not isinstance(value, Mapping) or set(value) != {"supported", "reason"}:
        raise ValueError("critic response schema mismatch")
    if not isinstance(value["supported"], bool) or not isinstance(value["reason"], str):
        raise ValueError("critic response has invalid field types")
    return _Critique(supported=value["supported"], reason=value["reason"])


def _response_text(response: Mapping[str, Any]) -> str:
    try:
        content = response["output"]["message"]["content"]
        blocks = [item["text"] for item in content if "text" in item]
    except (KeyError, TypeError) as exc:
        raise ValueError("Bedrock response did not contain assistant text") from exc
    if len(blocks) != 1 or not isinstance(blocks[0], str):
        raise ValueError("Bedrock response must contain exactly one text block")
    return blocks[0]


def _accepted_result(
    request: AssemblyRequest,
    draft: _Draft,
    revision_count: int,
) -> AssemblyResult:
    return AssemblyResult(
        utterance_id=request.utterance_id,
        status=AssemblyStatus.CONFIDENT,
        caption=draft.caption,
        tts_text=draft.tts_text,
        gloss_trace=request.evidence,
        confidence=min(item.confidence for item in request.evidence),
        source="bedrock_converse",
        revision_count=revision_count,
    )
