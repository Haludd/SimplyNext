"""Grounded caption assembly with an exact-template default."""

from .assembler import (
    AssemblyRequest,
    AssemblyResult,
    AssemblyStatus,
    CaptionAssembler,
    CaptionTemplate,
    DeterministicTemplateAssembler,
    GlossAlternativeEvidence,
    GlossEvidence,
    repair_result,
)
from .bedrock import (
    BEDROCK_MODEL_ID_ENV,
    BEDROCK_REGION_ENV,
    MAX_ALLOWED_REVISIONS,
    BedrockAssemblerConfig,
    BedrockCaptionAssembler,
    ConverseClient,
    create_bedrock_client,
)

__all__ = [
    "BEDROCK_MODEL_ID_ENV",
    "BEDROCK_REGION_ENV",
    "MAX_ALLOWED_REVISIONS",
    "AssemblyRequest",
    "AssemblyResult",
    "AssemblyStatus",
    "BedrockAssemblerConfig",
    "BedrockCaptionAssembler",
    "CaptionAssembler",
    "CaptionTemplate",
    "ConverseClient",
    "DeterministicTemplateAssembler",
    "GlossAlternativeEvidence",
    "GlossEvidence",
    "create_bedrock_client",
    "repair_result",
]
