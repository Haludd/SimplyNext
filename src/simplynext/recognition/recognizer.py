"""Recognizer interface and safe unconfigured implementation."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .types import RecognitionMetadata, RecognitionResult


@runtime_checkable
class Recognizer(Protocol):
    """Common surface for template and trained temporal recognizers."""

    @property
    def metadata(self) -> RecognitionMetadata:
        """Describe whether the recognizer is safe to use."""

        ...

    def recognize(self, sequence: Any, *, top_k: int = 3) -> RecognitionResult:
        """Return ranked hypotheses without making the acceptance decision."""

        ...


class UnconfiguredRecognizer:
    """Fail-closed recognizer used until a versioned model bundle is loaded.

    It intentionally ignores its input and never manufactures a placeholder sign.
    """

    def __init__(self, *, issue: str = "recognizer_unconfigured") -> None:
        self._metadata = RecognitionMetadata(
            ready=False,
            calibrated=False,
            schema_version=None,
            model_version=None,
            issues=(issue,),
        )

    @property
    def metadata(self) -> RecognitionMetadata:
        return self._metadata

    def recognize(self, sequence: Any, *, top_k: int = 3) -> RecognitionResult:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        return RecognitionResult(candidates=(), metadata=self._metadata)
