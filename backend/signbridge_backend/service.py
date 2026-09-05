"""Application service joining validation, analysis, and storage."""

from __future__ import annotations

from typing import Any

from .analyzer import SignAnalyzer
from .emotion import DeepFaceEmotionAnalyzer
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
        self.emotion_analyzer = emotion_analyzer or DeepFaceEmotionAnalyzer()

    def analyze(self, payload: SignSequencePayload) -> dict[str, Any]:
        result = self.analyzer.analyze(payload)
        if self.store is not None:
            self.store.append(payload, result)
        return result

    def analyze_emotion(self, image_bytes: bytes) -> dict[str, Any]:
        return self.emotion_analyzer.analyze(image_bytes)
