from __future__ import annotations

import json
import logging

from simplynext.agent import (
    AssemblyRequest,
    AssemblyStatus,
    BedrockAssemblerConfig,
    BedrockCaptionAssembler,
    CaptionTemplate,
    DeterministicTemplateAssembler,
    GlossEvidence,
)


def _request(*glosses: str) -> AssemblyRequest:
    return AssemblyRequest(
        utterance_id="utt-008",
        language="en",
        evidence=tuple(
            GlossEvidence(f"evidence-{index}", gloss, 0.95 - index * 0.01)
            for index, gloss in enumerate(glosses)
        ),
    )


def _model_response(payload: dict[str, object]) -> dict[str, object]:
    return {
        "output": {
            "message": {
                "content": [{"text": json.dumps(payload)}],
            }
        },
        "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
    }


def _draft(
    caption: str = "Water, please.",
    *,
    ids: list[str] | None = None,
    glosses: list[str] | None = None,
) -> dict[str, object]:
    return {
        "caption": caption,
        "tts_text": caption,
        "used_evidence_ids": ids or ["evidence-0", "evidence-1"],
        "used_glosses": glosses or ["WATER", "PLEASE"],
    }


class FakeConverseClient:
    def __init__(self, *responses: dict[str, object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def test_exact_template_assembler_only_emits_configured_sequence() -> None:
    assembler = DeterministicTemplateAssembler(
        {
            ("WATER", "PLEASE"): CaptionTemplate(
                caption="Water, please.",
                tts_text="Water, please.",
            )
        }
    )

    accepted = assembler.assemble(_request("WATER", "PLEASE"))
    refused = assembler.assemble(_request("PLEASE", "WATER"))

    assert accepted.status is AssemblyStatus.CONFIDENT
    assert accepted.caption == "Water, please."
    assert accepted.source == "exact_template"
    assert refused.status is AssemblyStatus.REPAIR_REQUIRED
    assert refused.caption is None
    assert refused.reason_codes == ("exact_caption_template_not_configured",)


def test_bedrock_assembler_uses_typed_evidence_and_logs_every_call(caplog) -> None:
    client = FakeConverseClient(
        _model_response(_draft()),
        _model_response({"supported": True, "reason": "fully supported"}),
    )
    assembler = BedrockCaptionAssembler(
        client,
        BedrockAssemblerConfig(model_id="configured-model-id"),
    )

    with caplog.at_level(logging.INFO, logger="simplynext.agent.bedrock"):
        result = assembler.assemble(_request("WATER", "PLEASE"))

    assert result.status is AssemblyStatus.CONFIDENT
    assert result.caption == "Water, please."
    assert len(client.calls) == 2
    assert (
        len([record for record in caplog.records if "bedrock_converse_usage" in record.message])
        == 2
    )
    serialized_calls = json.dumps(client.calls).lower()
    assert "landmark" not in serialized_calls
    assert "coordinates" not in serialized_calls
    assert "configured-model-id" in serialized_calls


def test_bedrock_assembler_allows_at_most_one_revision() -> None:
    client = FakeConverseClient(
        _model_response(_draft(ids=["unsupported-id"])),
        _model_response(_draft()),
        _model_response({"supported": True, "reason": "supported after correction"}),
    )
    assembler = BedrockCaptionAssembler(
        client,
        BedrockAssemblerConfig(model_id="configured-model-id", max_revisions=1),
    )

    result = assembler.assemble(_request("WATER", "PLEASE"))

    assert result.status is AssemblyStatus.CONFIDENT
    assert result.revision_count == 1
    assert len(client.calls) == 3


def test_bedrock_assembler_refuses_when_critic_rejects_the_only_revision() -> None:
    client = FakeConverseClient(
        _model_response(_draft("Could I have water, please?")),
        _model_response({"supported": False, "reason": "unsupported question intent"}),
        _model_response(_draft()),
        _model_response({"supported": False, "reason": "still unsupported"}),
    )
    assembler = BedrockCaptionAssembler(
        client,
        BedrockAssemblerConfig(model_id="configured-model-id", max_revisions=1),
    )

    result = assembler.assemble(_request("WATER", "PLEASE"))

    assert result.status is AssemblyStatus.REPAIR_REQUIRED
    assert result.caption is None
    assert result.revision_count == 1
    assert result.reason_codes == ("critic_rejected_caption",)
    assert len(client.calls) == 4


def test_bedrock_failures_return_repair_instead_of_model_text() -> None:
    client = FakeConverseClient(
        _model_response({"caption": "invented"}),
        _model_response({"caption": "invented again"}),
    )
    assembler = BedrockCaptionAssembler(
        client,
        BedrockAssemblerConfig(model_id="configured-model-id", max_revisions=1),
    )

    result = assembler.assemble(_request("WATER", "PLEASE"))

    assert result.status is AssemblyStatus.REPAIR_REQUIRED
    assert result.caption is None
    assert result.revision_count == 1
    assert len(client.calls) == 2
