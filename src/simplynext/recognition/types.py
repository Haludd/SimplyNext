"""Typed, dependency-free contracts for temporal recognition.

The recognition layer deliberately depends on a small feature-sequence contract rather
than the camera or normalization implementations.  ``coerce_feature_sequence`` accepts
the structural output produced by the pipeline while keeping recognition independently
testable.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any


class FeatureSequenceError(ValueError):
    """Raised when temporal features are missing or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class FeatureSequence:
    """A time-major feature matrix and a same-shaped validity mask."""

    feature_names: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    mask: tuple[tuple[bool, ...], ...]
    timestamps_ms: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.feature_names:
            raise FeatureSequenceError("feature_names must not be empty")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise FeatureSequenceError("feature_names must be unique")
        if len(self.values) != len(self.mask):
            raise FeatureSequenceError("values and mask must have the same frame count")

        width = len(self.feature_names)
        for frame_index, (row, row_mask) in enumerate(zip(self.values, self.mask, strict=True)):
            if len(row) != width or len(row_mask) != width:
                raise FeatureSequenceError(
                    f"frame {frame_index} does not match the {width}-feature schema"
                )
            if any(
                valid and not math.isfinite(value)
                for value, valid in zip(row, row_mask, strict=True)
            ):
                raise FeatureSequenceError(f"frame {frame_index} marks a non-finite value as valid")

        if self.timestamps_ms and len(self.timestamps_ms) != len(self.values):
            raise FeatureSequenceError(
                "timestamps_ms must be empty or have one timestamp per frame"
            )
        if any(
            current <= previous
            for previous, current in zip(
                self.timestamps_ms,
                self.timestamps_ms[1:],
                strict=False,
            )
        ):
            raise FeatureSequenceError("timestamps_ms must be strictly increasing")

    @property
    def frame_count(self) -> int:
        return len(self.values)

    @property
    def feature_count(self) -> int:
        return len(self.feature_names)

    @property
    def coverage(self) -> float:
        total = self.frame_count * self.feature_count
        if total == 0:
            return 0.0
        return sum(sum(row) for row in self.mask) / total

    @property
    def duration_ms(self) -> int | None:
        if len(self.timestamps_ms) < 2:
            return None
        return self.timestamps_ms[-1] - self.timestamps_ms[0]

    def reordered(self, target_names: Sequence[str]) -> FeatureSequence:
        """Return a copy in ``target_names`` order, rejecting schema drift."""

        target = tuple(target_names)
        if target == self.feature_names:
            return self
        if len(target) != len(self.feature_names) or set(target) != set(self.feature_names):
            raise FeatureSequenceError("feature schema does not match the model bundle")
        index_by_name = {name: index for index, name in enumerate(self.feature_names)}
        indices = tuple(index_by_name[name] for name in target)
        return replace(
            self,
            feature_names=target,
            values=tuple(tuple(row[index] for index in indices) for row in self.values),
            mask=tuple(tuple(row[index] for index in indices) for row in self.mask),
        )

    @classmethod
    def from_rows(
        cls,
        rows: Sequence[Sequence[float | int | None]],
        *,
        feature_names: Sequence[str] | None = None,
        mask: Sequence[Sequence[bool]] | None = None,
        timestamps_ms: Sequence[int] | None = None,
    ) -> FeatureSequence:
        raw_rows = tuple(tuple(row) for row in rows)
        if feature_names is None:
            width = len(raw_rows[0]) if raw_rows else 0
            feature_names = tuple(f"feature_{index}" for index in range(width))
        names = tuple(str(name) for name in feature_names)

        if mask is not None and len(mask) != len(raw_rows):
            raise FeatureSequenceError("mask must have one row per feature row")

        clean_values: list[tuple[float, ...]] = []
        clean_masks: list[tuple[bool, ...]] = []
        for row_index, row in enumerate(raw_rows):
            explicit_mask = tuple(mask[row_index]) if mask is not None else None
            if explicit_mask is not None and len(explicit_mask) != len(row):
                raise FeatureSequenceError(f"mask row {row_index} has the wrong width")

            value_row: list[float] = []
            mask_row: list[bool] = []
            for column_index, raw_value in enumerate(row):
                value = 0.0
                finite = False
                if raw_value is not None:
                    try:
                        value = float(raw_value)
                    except (TypeError, ValueError) as exc:
                        raise FeatureSequenceError(
                            f"feature at row {row_index}, column {column_index} is not numeric"
                        ) from exc
                    finite = math.isfinite(value)
                requested = bool(explicit_mask[column_index]) if explicit_mask is not None else True
                value_row.append(value if finite else 0.0)
                mask_row.append(requested and finite)
            clean_values.append(tuple(value_row))
            clean_masks.append(tuple(mask_row))

        return cls(
            feature_names=names,
            values=tuple(clean_values),
            mask=tuple(clean_masks),
            timestamps_ms=tuple(int(value) for value in (timestamps_ms or ())),
        )


def coerce_feature_sequence(value: Any) -> FeatureSequence:
    """Adapt a pipeline object or mapping to :class:`FeatureSequence`.

    The preferred pipeline surface is ``feature_names``, ``values``, ``mask`` and
    ``timestamps_ms``.  Mappings with those keys are accepted for replay fixtures and API
    tests.  No camera or landmark object is accepted here; normalization must happen first.
    """

    if isinstance(value, FeatureSequence):
        return value

    if isinstance(value, Mapping):
        feature_names = value.get("feature_names")
        rows = value.get("values")
        mask = value.get("mask")
        timestamps = value.get("timestamps_ms")
    else:
        feature_names = getattr(value, "feature_names", None)
        rows = getattr(value, "values", None)
        mask = getattr(value, "mask", None)
        timestamps = getattr(value, "timestamps_ms", None)

    if rows is None:
        raise FeatureSequenceError(
            "recognition expects normalized temporal features with a values matrix"
        )
    return FeatureSequence.from_rows(
        rows,
        feature_names=feature_names,
        mask=mask,
        timestamps_ms=timestamps,
    )


@dataclass(frozen=True, slots=True)
class RecognitionCandidate:
    """One closed-vocabulary hypothesis returned by a recognizer."""

    gloss: str
    confidence: float
    distance: float | None = None
    template_id: str | None = None

    def __post_init__(self) -> None:
        if not self.gloss or not self.gloss.strip():
            raise ValueError("gloss must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.distance is not None and (not math.isfinite(self.distance) or self.distance < 0.0):
            raise ValueError("distance must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class RecognitionMetadata:
    """Model readiness and calibration facts carried with every result."""

    ready: bool
    calibrated: bool
    schema_version: int | None
    model_version: str | None
    language: str | None = None
    vocabulary: tuple[str, ...] = ()
    template_count: int = 0
    feature_names: tuple[str, ...] = ()
    calibration_method: str | None = None
    issues: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecognitionResult:
    """A non-authoritative list of hypotheses plus model quality metadata."""

    candidates: tuple[RecognitionCandidate, ...]
    metadata: RecognitionMetadata
    input_coverage: float = 0.0
    frame_count: int = 0
    duration_ms: int | None = None

    @property
    def top_candidate(self) -> RecognitionCandidate | None:
        return self.candidates[0] if self.candidates else None
