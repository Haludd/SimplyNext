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
    GlossAlternativeEvidence,
    GlossEvidence,
)
from simplynext.contracts import (
    ClassifierDescriptor,
    GlossCandidate,
    GlossLattice,
    GlossLatticeProducer,
    GlossLatticeSlot,
    GlossProvenance,
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


def test_bedrock_prompt_retains_full_lattice_slot_evidence() -> None:
    profile = ClassifierDescriptor(
        name="temporal-classifier",
        model_version="asl-v3",
        calibration_version="temperature-v2",
        vocabulary_version="demo-v1",
    )
    lattice = GlossLattice(
        session_id="12345678-1234-5678-1234-567812345678",
        lattice_seq=7,
        utterance_id="utt-lattice-1",
        revision=1,
        language="asl",
        subject_id="signer-a",
        is_final=True,
        capture_start_ms=1_000,
        capture_end_ms=1_450,
        produced_ms=1_500,
        producer=GlossLatticeProducer(
            classifier=profile,
            segmenter_version="segmenter-v2",
            top_k=2,
        ),
        slots=(
            GlossLatticeSlot(
                slot_id="slot-0",
                start_ms=1_000,
                end_ms=1_450,
                candidates=(
                    GlossCandidate(rank=1, gloss="DRINK", confidence=0.55),
                    GlossCandidate(rank=2, gloss="WATER", confidence=0.45),
                ),
                resolved_gloss="WATER",
                selected_rank=2,
                provenance=GlossProvenance.TOP_K_SIGNER_CONFIRMED,
                confirmed_at_ms=1_480,
            ),
        ),
    )
    request = AssemblyRequest(
        utterance_id="utt-lattice-1",
        language="asl",
        subject_id="signer-a",
        lattice_seq=7,
        revision=1,
        classifier_model_version="asl-v3",
        calibration_version="temperature-v2",
        vocabulary_version="demo-v1",
        lattice=lattice,
        evidence=(
            GlossEvidence(
                evidence_id="slot-0",
                slot_id="slot-0",
                gloss="WATER",
                confidence=0.45,
                source="top_k_signer_confirmed",
                start_ms=1_000,
                end_ms=1_450,
                alternatives=(
                    GlossAlternativeEvidence(1, "DRINK", 0.55),
                    GlossAlternativeEvidence(2, "WATER", 0.45),
                ),
            ),
        ),
    )
    client = FakeConverseClient(
        _model_response(
            _draft(
                "Water.",
                ids=["slot-0"],
                glosses=["WATER"],
            )
        ),
        _model_response({"supported": True, "reason": "supported"}),
    )
    assembler = BedrockCaptionAssembler(
        client,
        BedrockAssemblerConfig(model_id="configured-model-id"),
    )

    result = assembler.assemble(request)

    assert result.status is AssemblyStatus.CONFIDENT
    prompt_text = client.calls[0]["messages"][0]["content"][0]["text"]
    prompt = json.loads(prompt_text)
    serialized_request = prompt["request"]
    assert serialized_request["lattice_seq"] == 7
    assert serialized_request["revision"] == 1
    assert serialized_request["producer"]["classifier"]["calibration_version"] == ("temperature-v2")
    assert serialized_request["slots"][0]["provenance"] == "top_k_signer_confirmed"
    assert serialized_request["slots"][0]["confirmed_at_ms"] == 1_480
    assert serialized_request["slots"][0]["candidates"] == [
        {"rank": 1, "gloss": "DRINK", "confidence": 0.55},
        {"rank": 2, "gloss": "WATER", "confidence": 0.45},
    ]
    assert "landmarks" not in json.dumps(serialized_request).lower()


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
