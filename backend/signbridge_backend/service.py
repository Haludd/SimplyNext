"""Application service joining validation, analysis, and storage."""

from __future__ import annotations

from typing import Any

from .analyzer import SignAnalyzer
from .emotion import DeepFaceEmotionAnalyzer
from .hsemotion import (
    HSEmotionAnalysisError,
    HSEmotionDependenciesMissing,
    HSEmotionEmotionAnalyzer,
    HSEmotionModelUnavailable,
)
from .models import SignSequencePayload
from .store import SequenceStore


class SignBridgeBackend:
    def __init__(
        self,
        analyzer: SignAnalyzer | None = None,
        store: SequenceStore | None = None,
        emotion_analyzer: DeepFaceEmotionAnalyzer | None = None,
    ) -> None:
        self.analyzer = analyzer or SignAnalyzer()
        self.store = store
        self.emotion_analyzer = emotion_analyzer or HSEmotionEmotionAnalyzer()
        self.deepface_fallback = DeepFaceEmotionAnalyzer()

    def analyze(self, payload: SignSequencePayload) -> dict[str, Any]:
        result = self.analyzer.analyze(payload)
        if self.store is not None:
            self.store.append(payload, result)
        return result

    def analyze_emotion(self, image_bytes: bytes) -> dict[str, Any]:
        try:
            face_result = self.emotion_analyzer.analyze(image_bytes)
        except (HSEmotionDependenciesMissing, HSEmotionModelUnavailable) as error:
            face_result = self.deepface_fallback.analyze(image_bytes)
            face_result["fallback"] = "hsemotion_unavailable"
            face_result["fallback_detail"] = str(error)
        except HSEmotionAnalysisError:
            raise
        return face_result

    def warm_up_emotion_models(self) -> None:
        """Load the face model before the first browser request."""
        try:
            self.emotion_analyzer.warm_up()
        except (HSEmotionDependenciesMissing, HSEmotionModelUnavailable):
            self.emotion_analyzer = self.deepface_fallback
            self.emotion_analyzer.warm_up()
