"""Replaceable baseline analyzer for hand, motion, and face features."""

from __future__ import annotations

import math
from typing import Any

from .classifier_features import ClassifierFeatureEngine
from .models import SignSequencePayload
from .processing_contracts import build_gloss_lattice
from .segmentation import PhraseSegmenter, create_segmenter
from .temporal_classifier import TemporalPrototypeClassifier


class SignAnalyzer:
    """A safe closed-vocabulary baseline until a trained model is available.

    This intentionally returns a candidate handshape instead of pretending that
    a few geometric thresholds are a complete ASL translator. A trained
    sequence model can implement the same ``analyze`` method later.
    """

    def __init__(
        self,
        model_version: str = "heuristic-signbridge-v2",
        temporal_classifier: TemporalPrototypeClassifier | None = None,
        segmenter: Any | None = None,
        segmenter_arm: str = "geometry_hysteresis",
    ) -> None:
        self.model_version = model_version
        self.segmenter = segmenter or create_segmenter(segmenter_arm)
        self.classifier_features = ClassifierFeatureEngine()
        self.temporal_classifier = temporal_classifier

    def analyze(self, payload: SignSequencePayload) -> dict[str, Any]:
        tracked_frames = [
            frame for frame in payload.frames if frame.get("hands")
        ]
        if not tracked_frames:
            return {
                "status": "no_signal",
                "gesture_label": "No hand signal",
                "caption": "Show your hands to begin tracking.",
                "confidence": 0.0,
                "gloss_trace": [],
                "detail": "No hand landmarks were present in the sequence.",
                "non_manual": self._non_manual_features({}, payload.face_analysis),
                "model_version": self.model_version,
                "language": payload.language,
                "segmentation": {
                    "phrase_count": 0,
                    "phrases": [],
                    "thresholds": self.segmenter.thresholds(),
                },
                "classifier_phrases": [],
                "feature_windows": [],
                "boundary_events": [],
                "top_k_glosses": [],
                "class_scores": {},
                "gloss_lattice": [],
                "gloss_lattice_message": build_gloss_lattice(
                    session_id=payload.session_id,
                    utterance_id=payload.sequence_id,
                    language=payload.language,
                    started_at=payload.started_at,
                    ended_at=payload.ended_at,
                    phrases=[],
                    producer=self._producer_metadata(payload),
                ),
            }

        segments = self.segmenter.segment(payload.frames)
        feature_windows = [
            self.classifier_features.build_feature_window(segment).to_dict()
            for segment in segments
        ]
        classifier_phrases = []
        for segment, feature_window in zip(segments, feature_windows):
            phrase = self.classifier_features.extract(
                segment.frames,
                phrase_id=segment.phrase_id,
                prior_frames=payload.frames[: segment.start_index],
            )
            classifier_output = self._classify_phrase(phrase)
            top_k = classifier_output["top_k_glosses"]
            class_scores = classifier_output["class_scores"]
            phrase["feature_window"] = feature_window
            phrase["top_k_glosses"] = top_k
            phrase["class_scores"] = class_scores
            classifier_output["schema_version"] = "1.0"
            classifier_output["feature_window_id"] = feature_window["window_id"]
            phrase["classifier_output"] = classifier_output
            classifier_phrases.append(phrase)
        boundary_events = [
            event.to_dict()
            for segment in segments
            for event in (segment.boundary_events or [])
        ]
        boundary_events.extend(
            event.to_dict()
            for event in getattr(self.segmenter, "last_events", [])
            if event.event_type == "stale_state"
        )
        top_k_glosses = classifier_phrases[-1]["top_k_glosses"] if classifier_phrases else []
        class_scores = classifier_phrases[-1]["class_scores"] if classifier_phrases else {}
        gloss_lattice = [
            {
                "slot": phrase["phrase_id"],
                "frame_range": phrase["feature_window"]["frame_range"],
                "top_k_glosses": phrase["top_k_glosses"],
                "class_scores": phrase["class_scores"],
                "confidence": phrase["top_k_glosses"][0]["confidence"]
                if phrase["top_k_glosses"] else 0.0,
                "provenance": phrase["classifier_output"]["provenance"],
                "baseline": phrase["classifier_output"].get("baseline"),
                "refused": phrase["classifier_output"].get("refused", False),
                "calibrated": phrase["classifier_output"].get("calibrated", False),
            }
            for phrase in classifier_phrases
        ]
        gloss_lattice_message = build_gloss_lattice(
            session_id=payload.session_id,
            utterance_id=payload.sequence_id,
            language=payload.language,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            phrases=classifier_phrases,
            producer=self._producer_metadata(payload),
        )
        latest = tracked_frames[-1]
        hands = latest.get("hands", [])
        openness_values = [self._hand_openness(hand) for hand in hands]
        openness_values = [value for value in openness_values if value is not None]
        motion = latest.get("hand_motion") or {}
        openness = (
            sum(openness_values) / len(openness_values)
            if openness_values
            else float(motion.get("average_openness", 0.0) or 0.0)
        )
        speed = float(motion.get("average_speed", 0.0) or 0.0)
        label = self._gesture_label(openness)
        if classifier_phrases:
            proposed_shape = classifier_phrases[-1]["classifier_handshape"]
            if proposed_shape != "UNKNOWN_HANDSHAPE":
                label = proposed_shape.lower().replace("_", " ")
        tracking_confidence = float(latest.get("tracking_confidence", 0.0) or 0.0)
        confidence = max(0.0, min(0.99, tracking_confidence * 0.65 + (0.35 if openness > 0.1 else 0.12)))
        face = latest.get("face_expression") or {}
        non_manual = self._non_manual_features(face, payload.face_analysis)
        face_label = str(non_manual["label"])

        return {
            "status": "candidate",
            "gesture_label": label,
            "caption": "Hand sequence captured — review candidate before translation.",
            "confidence": round(confidence, 4),
            "gloss_trace": [label.upper()],
            "detail": (
                f"{len(tracked_frames)} frames · {len(hands)} hand(s) · "
                f"{speed:.2f} motion · face {face_label} · "
                f"{non_manual['question_type']} · {len(segments)} phrase(s) · "
                "heuristic baseline, not a trained ASL translation model."
            ),
            "non_manual": non_manual,
            "model_version": self.model_version,
            "language": payload.language,
            "segmentation": {
                "phrase_count": len(segments),
                "phrases": [segment.to_dict() for segment in segments],
                "thresholds": self.segmenter.thresholds(),
            },
            "classifier_phrases": classifier_phrases,
            "feature_windows": feature_windows,
            "boundary_events": boundary_events,
            "top_k_glosses": top_k_glosses,
            "class_scores": class_scores,
            "gloss_lattice": gloss_lattice,
            "gloss_lattice_message": gloss_lattice_message,
        }

    def _producer_metadata(self, payload: SignSequencePayload) -> dict[str, Any]:
        calibrated = bool(
            self.temporal_classifier is not None
            and self.temporal_classifier.calibrator.fitted
        )
        return {
            "segmenter_arm": getattr(self.segmenter, "arm", "unknown"),
            "classifier_id": "signbridge_temporal_classifier",
            "classifier_version": self.model_version,
            "calibration_version": "temperature_v1" if calibrated else "none",
            "vocabulary_version": payload.lexicon_version,
        }

    def _classify_phrase(self, phrase: dict[str, Any]) -> dict[str, Any]:
        if self.temporal_classifier is not None and self.temporal_classifier.fitted:
            return self.temporal_classifier.predict(phrase["feature_sequence"])
        top_k, class_scores = self._top_k_glosses(phrase)
        return {
            "top_k_glosses": top_k,
            "class_scores": class_scores,
            "confidence": top_k[0]["confidence"] if top_k else 0.0,
            "provenance": "unresolved",
            "baseline": "geometric_baseline",
            "refused": True,
            "calibrated": False,
        }

    def _top_k_glosses(self, phrase: dict[str, Any], k: int = 3) -> tuple[list[dict[str, Any]], dict[str, float]]:
        """Return closed-vocabulary hypotheses, not an open-domain translation."""
        shape = str(phrase.get("classifier_handshape", "UNKNOWN_HANDSHAPE"))
        shape_confidence = self._bounded(phrase.get("handshape_confidence", 0.0))
        labels = (
            "1_HANDSHAPE",
            "3_HANDSHAPE",
            "C_HANDSHAPE",
            "OPEN_5_HANDSHAPE",
            "FIST_HANDSHAPE",
            "UNKNOWN_HANDSHAPE",
        )
        scores = {
            label: round(
                shape_confidence if label == shape else max(0.01, (1.0 - shape_confidence) * 0.22),
                6,
            )
            for label in labels
        }
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
        hypotheses = [
            {
                "rank": rank,
                "gloss_id": label,
                "gloss": label,
                "score": score,
                "confidence": score,
            }
            for rank, (label, score) in enumerate(ordered, start=1)
        ]
        return hypotheses, scores

    def _non_manual_features(
        self,
        face: dict[str, Any],
        external_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Expose the CV4ED affect result and neutral head-pose metadata.

        The browser deliberately does not infer emotions from blendshapes.
        It supplies only landmarks/head pose; CV4ED is the sole expression
        provider once a face crop has been analysed.
        """
        cv4ed_affect = face.get("cv4ed_affect") or external_analysis or {}
        if not isinstance(cv4ed_affect, dict):
            cv4ed_affect = {}
        model_label = cv4ed_affect.get("label") or face.get("label", "none")
        model_provider = cv4ed_affect.get("provider") or "cv4ed_affect_pending"
        head_roll = face.get("head_roll", face.get("head_tilt", 0.0))
        head_pitch = face.get("head_pitch", 0.0)
        head_yaw = face.get("head_yaw", 0.0)
        scores = cv4ed_affect.get("scores", {})
        if not isinstance(scores, dict):
            scores = {}
        return {
            "label": str(model_label),
            "provider": str(model_provider),
            "question_type": "none",
            "question_yes_no": 0.0,
            "question_wh": 0.0,
            "head_roll": float(head_roll or 0.0),
            "head_pitch": float(head_pitch or 0.0),
            "head_yaw": float(head_yaw or 0.0),
            "gaze": {},
            "action_units": {},
            "emotion_scores": scores,
            "emotion_confidence": self._bounded(cv4ed_affect.get("confidence", 0.0)),
            "emotion_model": str(cv4ed_affect.get("model", "")),
            "valence": float(cv4ed_affect.get("valence", 0.0) or 0.0),
            "arousal": float(cv4ed_affect.get("arousal", 0.0) or 0.0),
            "epistemic": cv4ed_affect.get("epistemic", {}),
        }

    @staticmethod
    def _bounded(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value or 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def _gesture_label(self, openness: float) -> str:
        if openness >= 0.8:
            return "open hand"
        if openness <= 0.2:
            return "closed hand"
        if 0.35 <= openness <= 0.5:
            return "partial handshape"
        return "unknown handshape"

    def _hand_openness(self, hand: dict[str, Any]) -> float | None:
        landmarks = hand.get("landmarks", [])
        if len(landmarks) < 21:
            return None
        wrist = landmarks[0]
        tips = (4, 8, 12, 16, 20)
        mcps = (2, 5, 9, 13, 17)
        extended = 0
        for tip_index, mcp_index in zip(tips, mcps):
            if self._distance(landmarks[tip_index], wrist) > self._distance(landmarks[mcp_index], wrist) * 1.18:
                extended += 1
        return extended / len(tips)

    @staticmethod
    def _distance(first: dict[str, Any], second: dict[str, Any]) -> float:
        return math.sqrt(
            sum(
                (float(first[axis]) - float(second[axis])) ** 2
                for axis in ("x", "y", "z")
            )
        )
