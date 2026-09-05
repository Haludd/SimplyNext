"""Application service joining validation, analysis, and storage."""

from __future__ import annotations

from typing import Any

from .analyzer import SignAnalyzer
from .models import SignSequencePayload
from .store import SequenceStore


class SignBridgeBackend:
    def __init__(
        self,
        analyzer: SignAnalyzer | None = None,
        store: SequenceStore | None = None,
    ) -> None:
        self.analyzer = analyzer or SignAnalyzer()
        self.store = store

    def analyze(self, payload: SignSequencePayload) -> dict[str, Any]:
        result = self.analyzer.analyze(payload)
        if self.store is not None:
            self.store.append(payload, result)
        return result
