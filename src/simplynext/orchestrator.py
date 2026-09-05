"""End-to-end recognition, uncertainty policy, and caption assembly."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from time import perf_counter
from typing import Any

from simplynext.agent import (
    AssemblyRequest,
    AssemblyStatus,
    BedrockAssemblerConfig,
    BedrockCaptionAssembler,
    CaptionAssembler,
    CaptionTemplate,
    DeterministicTemplateAssembler,
    GlossAlternativeEvidence,
    GlossEvidence,
    create_bedrock_client,
)
from simplynext.config import Settings
from simplynext.contracts import (
    GlossCandidate,
    GlossHypothesis,
    GlossLattice,
    GlossProvenance,
    GlossSlot,
    LandmarkFrame,
    LatticeChoice,
    LatticeEvidenceTrace,
    LatticeRepairRequiredEvent,
    LatticeResultEvent,
    RepairRequiredEvent,
    SignLanguage,
    TranslationResult,
    TranslationStatus,
    UtteranceRequest,
    UtteranceResultEvent,
)
from simplynext.contracts import (
    RepairAction as ContractRepairAction,
)
from simplynext.observability import MetricsRegistry
from simplynext.pipeline import (
    NormalizationError,
    NormalizedSequence,
    normalize_sequence,
    resample_sequence,
    temporal_feature_names,
)
from simplynext.recognition import (
    ConfidencePolicy,
    ConfidenceThresholds,
    DecisionStatus,
    DtwTemplateRecognizer,
    RecognitionCandidate,
    RecognitionMetadata,
    RecognitionQuality,
    RecognitionResult,
    Recognizer,
    UnconfiguredRecognizer,
)
from simplynext.recognition import (
    RepairAction as RecognitionRepairAction,
)

logger = logging.getLogger(__name__)

_ACTION_MESSAGES: dict[ContractRepairAction, str] = {
    ContractRepairAction.REPEAT: "Please repeat the sign more slowly.",
    ContractRepairAction.FINGERSPELL: (
        "That sign is outside the current vocabulary. Please fingerspell it."
    ),
    ContractRepairAction.CHOOSE_CANDIDATE: "Please choose the intended sign.",
    ContractRepairAction.REPOSITION: (
        "Please keep both hands and shoulders visible, then try again."
    ),
    ContractRepairAction.RECONNECT: (
        "The landmark stream lost too many frames. Please reconnect and try again."
    ),
    ContractRepairAction.MODEL_UNAVAILABLE: "Recognition is not configured yet.",
    ContractRepairAction.ESCALATE: (
        "The system cannot translate this safely. Please use another communication method."
    ),
}


class TranslationEngine:
    """The only component allowed to turn motion evidence into user-visible text."""

    def __init__(
        self,
        *,
        recognizer: Recognizer,
        policy: ConfidencePolicy,
        assembler: CaptionAssembler,
        metrics: MetricsRegistry,
        target_frames: int = 32,
        model_language: SignLanguage | None = None,
    ) -> None:
        if target_frames < 2:
            raise ValueError("target_frames must be at least 2")
        self.recognizer = recognizer
        self.policy = policy
        self.assembler = assembler
        self.metrics = metrics
        self.target_frames = target_frames
        self.model_language = model_language

    @property
    def assembler_ready(self) -> bool:
        """Whether the selected caption path has usable configuration."""

        configured = getattr(self.assembler, "ready", True)
        return configured if isinstance(configured, bool) else False

    async def process_lattice(
        self,
        lattice: GlossLattice,
        *,
        signer_id: str | None = None,
    ) -> LatticeResultEvent | LatticeRepairRequiredEvent:
        """Run one already-classified lattice through the bounded Agent seam."""

        return await asyncio.to_thread(self._process_lattice, lattice, signer_id)

    def _process_lattice(
        self,
        lattice: GlossLattice,
        signer_id: str | None,
    ) -> LatticeResultEvent | LatticeRepairRequiredEvent:
        started = perf_counter()
        evidence_trace = _lattice_evidence_trace(lattice)
        classifier_version = lattice.producer.classifier_version
        for slot in lattice.slots:
            self.metrics.increment(f"lattice_provenance_{slot.provenance.value}")

        if self.model_language is not None and lattice.language is not self.model_language:
            return self._lattice_repair_event(
                lattice=lattice,
                action=ContractRepairAction.MODEL_UNAVAILABLE,
                confidence=0.0,
                reason_codes=("language_model_not_configured",),
                evidence_trace=evidence_trace,
                started=started,
            )
        thresholds = self.policy.thresholds
        duration_ms = lattice.ended_at_ms - lattice.started_at_ms
        if duration_ms < thresholds.min_duration_ms:
            return self._lattice_repair_event(
                lattice=lattice,
                action=ContractRepairAction.REPEAT,
                confidence=0.0,
                reason_codes=("utterance_too_short",),
                evidence_trace=evidence_trace,
                started=started,
            )
        if duration_ms > thresholds.max_duration_ms:
            return self._lattice_repair_event(
                lattice=lattice,
                action=ContractRepairAction.REPEAT,
                confidence=0.0,
                reason_codes=("utterance_too_long",),
                evidence_trace=evidence_trace,
                started=started,
            )
        unresolved = tuple(
            slot for slot in lattice.slots if slot.provenance is GlossProvenance.UNRESOLVED
        )
        if unresolved:
            target = unresolved[0]
            choices = _lattice_choices(target, target.candidates)
            action = (
                ContractRepairAction.CHOOSE_CANDIDATE
                if len(choices) >= 2
                else ContractRepairAction.FINGERSPELL
                if not choices
                else ContractRepairAction.REPEAT
            )
            return self._lattice_repair_event(
                lattice=lattice,
                action=action,
                confidence=(target.candidates[0].confidence if target.candidates else 0.0),
                choices=choices if action is ContractRepairAction.CHOOSE_CANDIDATE else (),
                target_slot_ids=tuple(slot.slot_id for slot in unresolved),
                reason_codes=("unresolved_lattice_slot",),
                evidence_trace=evidence_trace,
                started=started,
            )

        rejected_glosses = {_canonical_gloss(value) for value in thresholds.rejected_glosses}
        for slot in lattice.slots:
            if slot.provenance is not GlossProvenance.CLASSIFIER_HIGH_CONFIDENCE:
                continue
            selected = slot.candidates[0]
            canonical = _canonical_gloss(selected.gloss_id)
            if canonical in rejected_glosses:
                action = (
                    ContractRepairAction.FINGERSPELL
                    if canonical in {"UNKNOWN", "OOV"}
                    else ContractRepairAction.REPEAT
                )
                return self._lattice_repair_event(
                    lattice=lattice,
                    action=action,
                    confidence=selected.confidence,
                    target_slot_ids=(slot.slot_id,),
                    reason_codes=(f"rejected_class:{canonical.lower()}",),
                    evidence_trace=evidence_trace,
                    started=started,
                )
            if selected.confidence < thresholds.min_top1_confidence:
                viable = tuple(
                    item
                    for item in slot.candidates
                    if item.confidence >= thresholds.min_candidate_choice_confidence
                )
                choices = _lattice_choices(slot, viable)
                action = (
                    ContractRepairAction.CHOOSE_CANDIDATE
                    if len(choices) >= 2
                    else ContractRepairAction.REPEAT
                )
                return self._lattice_repair_event(
                    lattice=lattice,
                    action=action,
                    confidence=selected.confidence,
                    choices=(choices if action is ContractRepairAction.CHOOSE_CANDIDATE else ()),
                    target_slot_ids=(slot.slot_id,),
                    reason_codes=("classifier_provenance_below_threshold",),
                    evidence_trace=evidence_trace,
                    started=started,
                )
            if len(slot.candidates) >= 2:
                margin = selected.confidence - slot.candidates[1].confidence
                if margin < thresholds.min_top1_top2_margin:
                    choices = _lattice_choices(slot, slot.candidates[:2])
                    return self._lattice_repair_event(
                        lattice=lattice,
                        action=ContractRepairAction.CHOOSE_CANDIDATE,
                        confidence=selected.confidence,
                        choices=choices,
                        target_slot_ids=(slot.slot_id,),
                        reason_codes=("classifier_provenance_ambiguous",),
                        evidence_trace=evidence_trace,
                        started=started,
                    )

        request = AssemblyRequest(
            utterance_id=lattice.utterance_id,
            language=str(lattice.language),
            evidence=tuple(_assembly_evidence(slot) for slot in lattice.slots),
            signer_id=signer_id,
            lattice_seq=lattice.lattice_seq,
            classifier_version=classifier_version,
            calibration_version=lattice.producer.calibration_version,
            vocabulary_version=lattice.producer.vocabulary_version,
            lattice=lattice,
        )
        assemble_started = perf_counter()
        try:
            assembly = self.assembler.assemble(request)
        except Exception as exc:
            logger.exception(
                "lattice_assembly_failed",
                extra={"utterance_id": lattice.utterance_id, "reason": type(exc).__name__},
            )
            return self._lattice_repair_event(
                lattice=lattice,
                action=ContractRepairAction.ESCALATE,
                confidence=_minimum_lattice_confidence(lattice),
                target_slot_ids=tuple(slot.slot_id for slot in lattice.slots),
                reason_codes=("assembly_failed",),
                evidence_trace=evidence_trace,
                started=started,
                latency_ms={"assemble": _elapsed_ms(assemble_started)},
            )
        assemble_ms = _elapsed_ms(assemble_started)
        if assembly.status is AssemblyStatus.REPAIR_REQUIRED or assembly.caption is None:
            action = _contract_action(assembly.repair_action)
            first_slot = lattice.slots[0]
            choices = (
                _lattice_choices(first_slot, first_slot.candidates)
                if action is ContractRepairAction.CHOOSE_CANDIDATE
                else ()
            )
            if action is ContractRepairAction.CHOOSE_CANDIDATE and not choices:
                action = ContractRepairAction.REPEAT
            return self._lattice_repair_event(
                lattice=lattice,
                action=action,
                confidence=assembly.confidence,
                choices=choices,
                target_slot_ids=(
                    (first_slot.slot_id,)
                    if choices
                    else tuple(slot.slot_id for slot in lattice.slots)
                ),
                reason_codes=assembly.reason_codes,
                evidence_trace=evidence_trace,
                started=started,
                agent_source=assembly.source,
                latency_ms={"assemble": assemble_ms},
            )

        latency = {
            "assemble": assemble_ms,
            "total": _elapsed_ms(started),
        }
        event = LatticeResultEvent(
            lattice_seq=lattice.lattice_seq,
            utterance_id=lattice.utterance_id,
            caption=assembly.caption,
            tts_text=assembly.tts_text,
            confidence=assembly.confidence,
            gloss_id_trace=tuple(item.gloss_id for item in assembly.gloss_trace),
            evidence_trace=evidence_trace,
            classifier_version=classifier_version,
            agent_source=assembly.source,
            latency_ms=latency,
        )
        self.metrics.increment("lattice_utterances_confident")
        self.metrics.increment("utterances_confident")
        self.metrics.observe_ms("lattice_utterance_total", latency["total"])
        return event

    async def process_frames(
        self,
        *,
        utterance_id: str,
        language: SignLanguage,
        frames: Sequence[LandmarkFrame],
        dropped_frames: int = 0,
    ) -> UtteranceResultEvent | RepairRequiredEvent:
        """Normalize and recognize one completed raw landmark window off the event loop."""

        return await asyncio.to_thread(
            self._process_frames,
            utterance_id,
            language,
            tuple(frames),
            dropped_frames,
        )

    def _process_frames(
        self,
        utterance_id: str,
        language: SignLanguage,
        frames: tuple[LandmarkFrame, ...],
        dropped_frames: int,
    ) -> UtteranceResultEvent | RepairRequiredEvent:
        started = perf_counter()
        if self.model_language is not None and language is not self.model_language:
            return self._repair_event(
                utterance_id=utterance_id,
                action=ContractRepairAction.MODEL_UNAVAILABLE,
                confidence=0.0,
                reason_codes=("language_model_not_configured",),
                model_version=self.recognizer.metadata.model_version,
                started=started,
            )
        if len(frames) < 2:
            return self._repair_event(
                utterance_id=utterance_id,
                action=ContractRepairAction.REPEAT,
                confidence=0.0,
                reason_codes=("too_few_frames",),
                model_version=self.recognizer.metadata.model_version,
                started=started,
            )

        normalize_started = perf_counter()
        try:
            normalized = normalize_sequence(frames)
            features = resample_sequence(normalized, target_frames=self.target_frames)
        except (NormalizationError, ValueError) as exc:
            logger.info(
                "utterance_normalization_rejected",
                extra={"utterance_id": utterance_id, "reason": type(exc).__name__},
            )
            return self._repair_event(
                utterance_id=utterance_id,
                action=ContractRepairAction.REPOSITION,
                confidence=0.0,
                reason_codes=("normalization_failed",),
                model_version=self.recognizer.metadata.model_version,
                started=started,
            )
        normalize_ms = _elapsed_ms(normalize_started)

        recognize_started = perf_counter()
        try:
            result = self.recognizer.recognize(features, top_k=3)
            quality = RecognitionQuality(
                coverage=_critical_landmark_coverage(normalized),
                duration_ms=result.duration_ms,
                # Drop counts describe the raw transport, so their denominator must
                # also be raw frames rather than the fixed-size resampled sequence.
                received_frames=len(frames),
                dropped_frames=dropped_frames,
            )
            decision = self.policy.evaluate(result, quality)
        except Exception as exc:
            logger.exception(
                "utterance_recognition_failed",
                extra={"utterance_id": utterance_id, "reason": type(exc).__name__},
            )
            return self._repair_event(
                utterance_id=utterance_id,
                action=ContractRepairAction.MODEL_UNAVAILABLE,
                confidence=0.0,
                reason_codes=("recognition_failed",),
                model_version=self.recognizer.metadata.model_version,
                started=started,
                latency_ms={"normalize": normalize_ms},
            )
        recognize_ms = _elapsed_ms(recognize_started)
        if decision.status is DecisionStatus.REPAIR_REQUIRED or decision.accepted is None:
            return self._repair_event(
                utterance_id=utterance_id,
                action=_contract_action(decision.repair_action),
                confidence=result.top_candidate.confidence if result.top_candidate else 0.0,
                choices=decision.choices,
                reason_codes=decision.reason_codes,
                model_version=result.metadata.model_version,
                started=started,
                latency_ms={"normalize": normalize_ms, "recognize": recognize_ms},
            )

        assemble_started = perf_counter()
        try:
            assembly = self.assembler.assemble(
                AssemblyRequest(
                    utterance_id=utterance_id,
                    language=str(language),
                    evidence=(GlossEvidence.from_candidate("g0", decision.accepted),),
                )
            )
        except Exception as exc:
            logger.exception(
                "utterance_assembly_failed",
                extra={"utterance_id": utterance_id, "reason": type(exc).__name__},
            )
            return self._repair_event(
                utterance_id=utterance_id,
                action=ContractRepairAction.ESCALATE,
                confidence=decision.accepted.confidence,
                reason_codes=("assembly_failed",),
                model_version=result.metadata.model_version,
                started=started,
                latency_ms={"normalize": normalize_ms, "recognize": recognize_ms},
            )
        assemble_ms = _elapsed_ms(assemble_started)
        if assembly.status is AssemblyStatus.REPAIR_REQUIRED or assembly.caption is None:
            return self._repair_event(
                utterance_id=utterance_id,
                action=_contract_action(assembly.repair_action),
                confidence=assembly.confidence,
                choices=result.candidates,
                reason_codes=assembly.reason_codes,
                model_version=result.metadata.model_version,
                started=started,
                latency_ms={
                    "normalize": normalize_ms,
                    "recognize": recognize_ms,
                    "assemble": assemble_ms,
                },
            )

        latency = {
            "normalize": normalize_ms,
            "recognize": recognize_ms,
            "assemble": assemble_ms,
            "total": _elapsed_ms(started),
        }
        event = UtteranceResultEvent(
            utterance_id=utterance_id,
            caption=assembly.caption,
            tts_text=assembly.tts_text,
            confidence=assembly.confidence,
            gloss_trace=tuple(item.gloss_id for item in assembly.gloss_trace),
            hypotheses=_contract_hypotheses(result.candidates),
            model_version=result.metadata.model_version or "unknown",
            latency_ms=latency,
        )
        self.metrics.increment("utterances_confident")
        self.metrics.observe_ms("utterance_total", latency["total"])
        return event

    async def process_hypotheses(self, payload: UtteranceRequest) -> TranslationResult:
        """Run the legacy, already-classified utterance seam through the same safety policy."""

        return await asyncio.to_thread(self._process_hypotheses, payload)

    def _process_hypotheses(self, payload: UtteranceRequest) -> TranslationResult:
        if self.model_language is not None and payload.language is not self.model_language:
            self.metrics.increment("utterances_repair_required")
            return TranslationResult(
                utterance_id=payload.utterance_id,
                status=TranslationStatus.UNCERTAIN,
                confidence=0.0,
                repair_action=ContractRepairAction.MODEL_UNAVAILABLE,
                message=_ACTION_MESSAGES[ContractRepairAction.MODEL_UNAVAILABLE],
                reason_codes=("language_model_not_configured",),
            )
        candidates = tuple(
            RecognitionCandidate(item.gloss, item.confidence)
            for item in sorted(payload.hypotheses, key=lambda item: item.confidence, reverse=True)
        )
        feature_data = payload.features
        calibrated = feature_data.get("calibrated") is True
        model_version_value = feature_data.get("model_version")
        model_version = (
            str(model_version_value)
            if isinstance(model_version_value, (str, int, float))
            else "client-classifier"
        )
        duration_ms = int((payload.ended_at - payload.started_at).total_seconds() * 1000)
        frame_count = _safe_int(feature_data.get("frame_count"), default=0)
        dropped_frames = _safe_int(feature_data.get("dropped_frames"), default=0)
        coverage = _safe_fraction(feature_data.get("landmark_coverage"), default=0.0)
        result = RecognitionResult(
            candidates=candidates,
            metadata=RecognitionMetadata(
                ready=True,
                calibrated=calibrated,
                schema_version=1,
                model_version=model_version,
                vocabulary=tuple(item.gloss for item in candidates),
                issues=() if calibrated else ("client_confidence_not_calibrated",),
            ),
            input_coverage=coverage,
            frame_count=frame_count,
            duration_ms=duration_ms,
        )
        try:
            decision = self.policy.evaluate(
                result,
                RecognitionQuality.from_result(result, dropped_frames=dropped_frames),
            )
        except Exception as exc:
            logger.exception(
                "replay_policy_failed",
                extra={"utterance_id": payload.utterance_id, "reason": type(exc).__name__},
            )
            self.metrics.increment("utterances_repair_required")
            return TranslationResult(
                utterance_id=payload.utterance_id,
                status=TranslationStatus.UNCERTAIN,
                confidence=0.0,
                repair_action=ContractRepairAction.ESCALATE,
                message=_ACTION_MESSAGES[ContractRepairAction.ESCALATE],
                reason_codes=("policy_failed",),
                model_version=model_version,
            )
        if decision.status is DecisionStatus.REPAIR_REQUIRED or decision.accepted is None:
            action = _contract_action(decision.repair_action)
            self.metrics.increment("utterances_repair_required")
            return TranslationResult(
                utterance_id=payload.utterance_id,
                status=TranslationStatus.UNCERTAIN,
                confidence=candidates[0].confidence if candidates else 0.0,
                repair_action=action,
                message=_ACTION_MESSAGES[action],
                choices=_contract_hypotheses(decision.choices),
                reason_codes=decision.reason_codes,
                model_version=model_version,
            )

        try:
            assembly = self.assembler.assemble(
                AssemblyRequest(
                    utterance_id=payload.utterance_id,
                    language=str(payload.language),
                    evidence=(GlossEvidence.from_candidate("g0", decision.accepted),),
                )
            )
        except Exception as exc:
            logger.exception(
                "replay_assembly_failed",
                extra={"utterance_id": payload.utterance_id, "reason": type(exc).__name__},
            )
            self.metrics.increment("utterances_repair_required")
            return TranslationResult(
                utterance_id=payload.utterance_id,
                status=TranslationStatus.UNCERTAIN,
                confidence=decision.accepted.confidence,
                repair_action=ContractRepairAction.ESCALATE,
                message=_ACTION_MESSAGES[ContractRepairAction.ESCALATE],
                reason_codes=("assembly_failed",),
                model_version=model_version,
            )
        if assembly.status is AssemblyStatus.REPAIR_REQUIRED or assembly.caption is None:
            action = _contract_action(assembly.repair_action)
            self.metrics.increment("utterances_repair_required")
            return TranslationResult(
                utterance_id=payload.utterance_id,
                status=TranslationStatus.UNCERTAIN,
                confidence=assembly.confidence,
                repair_action=action,
                message=_ACTION_MESSAGES[action],
                choices=_contract_hypotheses(result.candidates),
                reason_codes=assembly.reason_codes,
                model_version=model_version,
            )
        self.metrics.increment("utterances_confident")
        return TranslationResult(
            utterance_id=payload.utterance_id,
            status=TranslationStatus.CONFIDENT,
            caption=assembly.caption,
            tts_text=assembly.tts_text,
            gloss_trace=tuple(item.gloss_id for item in assembly.gloss_trace),
            confidence=assembly.confidence,
            model_version=model_version,
        )

    def _lattice_repair_event(
        self,
        *,
        lattice: GlossLattice,
        action: ContractRepairAction,
        confidence: float,
        reason_codes: tuple[str, ...],
        evidence_trace: tuple[LatticeEvidenceTrace, ...],
        started: float,
        choices: tuple[LatticeChoice, ...] = (),
        target_slot_ids: tuple[str, ...] = (),
        agent_source: str | None = None,
        latency_ms: Mapping[str, int] | None = None,
    ) -> LatticeRepairRequiredEvent:
        latency = dict(latency_ms or {})
        latency["total"] = _elapsed_ms(started)
        self.metrics.increment("lattice_utterances_repair_required")
        self.metrics.increment("utterances_repair_required")
        self.metrics.increment(f"lattice_repair_{action.value}")
        self.metrics.observe_ms("lattice_utterance_total", latency["total"])
        return LatticeRepairRequiredEvent(
            lattice_seq=lattice.lattice_seq,
            utterance_id=lattice.utterance_id,
            action=action,
            message=_ACTION_MESSAGES[action],
            confidence=max(0.0, min(1.0, confidence)),
            target_slot_ids=target_slot_ids,
            choices=choices,
            reason_codes=reason_codes,
            evidence_trace=evidence_trace,
            classifier_version=lattice.producer.classifier_version,
            agent_source=agent_source,
            latency_ms=latency,
        )

    def _repair_event(
        self,
        *,
        utterance_id: str,
        action: ContractRepairAction,
        confidence: float,
        reason_codes: tuple[str, ...],
        model_version: str | None,
        started: float,
        choices: Sequence[RecognitionCandidate] = (),
        latency_ms: Mapping[str, int] | None = None,
    ) -> RepairRequiredEvent:
        latency = dict(latency_ms or {})
        latency["total"] = _elapsed_ms(started)
        self.metrics.increment("utterances_repair_required")
        self.metrics.observe_ms("utterance_total", latency["total"])
        return RepairRequiredEvent(
            utterance_id=utterance_id,
            action=action,
            message=_ACTION_MESSAGES[action],
            confidence=max(0.0, min(1.0, confidence)),
            choices=(
                _contract_hypotheses(choices)
                if action is ContractRepairAction.CHOOSE_CANDIDATE
                else ()
            ),
            reason_codes=reason_codes,
            model_version=model_version,
            latency_ms=latency,
        )


def build_translation_engine(settings: Settings, metrics: MetricsRegistry) -> TranslationEngine:
    recognizer: Recognizer = UnconfiguredRecognizer()
    if settings.template_bundle_path is not None:
        try:
            recognizer = DtwTemplateRecognizer.from_json(settings.template_bundle_path)
            if recognizer.metadata.language != settings.recognition_language.value:
                raise ValueError("recognition bundle language does not match configuration")
            expected_names = temporal_feature_names()
            actual_names = recognizer.metadata.feature_names
            if len(actual_names) != len(expected_names) or set(actual_names) != set(expected_names):
                raise ValueError("recognition bundle feature schema does not match the pipeline")
        except Exception as exc:
            logger.error(
                "recognizer_bundle_rejected",
                extra={"reason": type(exc).__name__},
            )
            recognizer = UnconfiguredRecognizer(issue="recognizer_bundle_invalid")

    assembler: CaptionAssembler
    if settings.bedrock_enabled:
        assembler = BedrockCaptionAssembler(
            create_bedrock_client(
                region_name=settings.aws_region,
                connect_timeout_seconds=settings.bedrock_connect_timeout_seconds,
                read_timeout_seconds=settings.bedrock_read_timeout_seconds,
                total_max_attempts=settings.bedrock_total_max_attempts,
            ),
            BedrockAssemblerConfig(
                model_id=settings.bedrock_model_id,
                max_revisions=settings.agent_max_revisions,
            ),
        )
    else:
        templates = _load_caption_templates(settings.caption_templates_path)
        assembler = DeterministicTemplateAssembler(templates)

    policy = ConfidencePolicy(
        ConfidenceThresholds(
            min_top1_confidence=settings.min_recognition_confidence,
            min_top1_top2_margin=settings.min_recognition_margin,
            min_coverage=settings.min_landmark_coverage,
        )
    )
    return TranslationEngine(
        recognizer=recognizer,
        policy=policy,
        assembler=assembler,
        metrics=metrics,
        model_language=settings.recognition_language,
    )


def _load_caption_templates(
    path: Path | None,
) -> dict[tuple[str, ...], CaptionTemplate]:
    if path is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
            raise ValueError("caption template schema_version must be '1.0'")
        raw_templates = payload.get("templates")
        if not isinstance(raw_templates, list):
            raise ValueError("caption templates must be an array")
        templates: dict[tuple[str, ...], CaptionTemplate] = {}
        for item in raw_templates:
            if not isinstance(item, dict) or set(item) - {"glosses", "caption", "tts_text"}:
                raise ValueError("caption template has an invalid shape")
            glosses = item.get("glosses")
            caption = item.get("caption")
            tts_text = item.get("tts_text")
            if not isinstance(glosses, list) or not all(
                isinstance(value, str) for value in glosses
            ):
                raise ValueError("caption template glosses must be strings")
            if not isinstance(caption, str) or (
                tts_text is not None and not isinstance(tts_text, str)
            ):
                raise ValueError("caption template text is invalid")
            key = tuple(glosses)
            if key in templates:
                raise ValueError("duplicate caption template")
            templates[key] = CaptionTemplate(caption=caption, tts_text=tts_text)
        return templates
    except (OSError, ValueError, TypeError) as exc:
        logger.error("caption_templates_rejected", extra={"reason": type(exc).__name__})
        return {}


def _contract_hypotheses(
    candidates: Sequence[RecognitionCandidate],
) -> tuple[GlossHypothesis, ...]:
    return tuple(
        GlossHypothesis(gloss=item.gloss, confidence=item.confidence) for item in candidates
    )


def _assembly_evidence(slot: GlossSlot) -> GlossEvidence:
    if slot.resolved_gloss_id is None:
        raise ValueError("unresolved lattice slots cannot enter caption assembly")
    resolved = slot.resolved_candidate
    confidence = resolved.confidence if resolved is not None else 1.0
    return GlossEvidence(
        evidence_id=slot.slot_id,
        gloss_id=slot.resolved_gloss_id,
        confidence=confidence,
        provenance=slot.provenance.value,
        slot_id=slot.slot_id,
        start_ms=slot.start_ms,
        end_ms=slot.end_ms,
        candidates=tuple(
            GlossAlternativeEvidence(
                rank=item.rank,
                gloss_id=item.gloss_id,
                confidence=item.confidence,
            )
            for item in slot.candidates
        ),
    )


def _lattice_evidence_trace(lattice: GlossLattice) -> tuple[LatticeEvidenceTrace, ...]:
    trace: list[LatticeEvidenceTrace] = []
    for slot in lattice.slots:
        resolved = slot.resolved_candidate
        trace.append(
            LatticeEvidenceTrace(
                slot_id=slot.slot_id,
                start_ms=slot.start_ms,
                end_ms=slot.end_ms,
                resolved_gloss_id=slot.resolved_gloss_id,
                confidence=resolved.confidence if resolved is not None else None,
                provenance=slot.provenance,
                candidates=slot.candidates,
            )
        )
    return tuple(trace)


def _lattice_choices(
    slot: GlossSlot,
    candidates: Sequence[GlossCandidate],
) -> tuple[LatticeChoice, ...]:
    return tuple(
        LatticeChoice(
            slot_id=slot.slot_id,
            rank=item.rank,
            gloss_id=item.gloss_id,
            confidence=item.confidence,
        )
        for item in candidates
    )


def _minimum_lattice_confidence(lattice: GlossLattice) -> float:
    confidences = tuple(
        slot.resolved_candidate.confidence
        for slot in lattice.slots
        if slot.resolved_candidate is not None
    )
    return min(confidences, default=1.0)


def _canonical_gloss(gloss: str) -> str:
    return gloss.strip().upper().replace(" ", "_")


def _critical_landmark_coverage(sequence: NormalizedSequence) -> float:
    """Require reliable pose plus at least one hand without rejecting one-handed signs."""

    pose = sequence.quality.for_group("pose").available_fraction
    left = sequence.quality.for_group("left_hand").available_fraction
    right = sequence.quality.for_group("right_hand").available_fraction
    return min(pose, max(left, right))


def _contract_action(action: RecognitionRepairAction | str | None) -> ContractRepairAction:
    raw = str(action) if action is not None else ContractRepairAction.REPEAT.value
    try:
        return ContractRepairAction(raw)
    except ValueError:
        return ContractRepairAction.REPEAT


def _safe_int(value: Any, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _safe_fraction(value: Any, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if 0.0 <= result <= 1.0 else default


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))
