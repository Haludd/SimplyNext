"""Mask-aware nearest-template recognition using dynamic time warping."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .types import (
    FeatureSequence,
    FeatureSequenceError,
    RecognitionCandidate,
    RecognitionMetadata,
    RecognitionResult,
    coerce_feature_sequence,
)

BUNDLE_SCHEMA_VERSION = 1


class TemplateBundleError(ValueError):
    """Raised when a template bundle is unsafe or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class DistanceCalibration:
    """Validated mapping from DTW distance to an acceptance confidence."""

    midpoint: float
    temperature: float
    validated: bool = False
    method: str = "distance_logistic"

    def __post_init__(self) -> None:
        if self.method != "distance_logistic":
            raise TemplateBundleError("only the distance_logistic calibration method is supported")
        if not math.isfinite(self.midpoint) or self.midpoint < 0.0:
            raise TemplateBundleError("calibration midpoint must be finite and non-negative")
        if not math.isfinite(self.temperature) or self.temperature <= 0.0:
            raise TemplateBundleError("calibration temperature must be positive")

    def confidence(self, distance: float) -> float:
        exponent = (distance - self.midpoint) / self.temperature
        if exponent >= 700.0:
            return 0.0
        if exponent <= -700.0:
            return 1.0
        return 1.0 / (1.0 + math.exp(exponent))


@dataclass(frozen=True, slots=True)
class SignTemplate:
    template_id: str
    gloss: str
    sequence: FeatureSequence

    def __post_init__(self) -> None:
        if not self.template_id.strip():
            raise TemplateBundleError("template id must not be empty")
        if not self.gloss.strip():
            raise TemplateBundleError("template gloss must not be empty")
        if self.sequence.frame_count == 0:
            raise TemplateBundleError("template sequence must contain at least one frame")


@dataclass(frozen=True, slots=True)
class TemplateBundle:
    schema_version: int
    model_version: str
    language: str
    feature_names: tuple[str, ...]
    templates: tuple[SignTemplate, ...]
    calibration: DistanceCalibration | None = None

    def __post_init__(self) -> None:
        if self.schema_version != BUNDLE_SCHEMA_VERSION:
            raise TemplateBundleError(
                f"unsupported bundle schema_version {self.schema_version!r}; "
                f"expected {BUNDLE_SCHEMA_VERSION}"
            )
        if not self.model_version.strip():
            raise TemplateBundleError("model_version must not be empty")
        if self.language not in {"asl", "sgsl"}:
            raise TemplateBundleError("language must be 'asl' or 'sgsl'")
        if not self.feature_names or len(set(self.feature_names)) != len(self.feature_names):
            raise TemplateBundleError("feature_names must be non-empty and unique")
        if not self.templates:
            raise TemplateBundleError("a bundle must contain at least one template")

        ids: set[str] = set()
        for template in self.templates:
            if template.template_id in ids:
                raise TemplateBundleError(f"duplicate template id {template.template_id!r}")
            ids.add(template.template_id)
            if template.sequence.feature_names != self.feature_names:
                raise TemplateBundleError(
                    f"template {template.template_id!r} has a different feature schema"
                )

    @property
    def vocabulary(self) -> tuple[str, ...]:
        return tuple(sorted({template.gloss for template in self.templates}))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> TemplateBundle:
        """Validate the public JSON bundle format and construct a bundle."""

        try:
            schema_version = int(payload["schema_version"])
            model_version = str(payload["model_version"])
            language = str(payload["language"]).strip().lower()
            feature_names = tuple(str(name) for name in payload["feature_names"])
            raw_templates = payload["templates"]
        except (KeyError, TypeError, ValueError) as exc:
            raise TemplateBundleError("bundle metadata is missing or invalid") from exc

        if not isinstance(raw_templates, list):
            raise TemplateBundleError("templates must be a JSON array")

        templates: list[SignTemplate] = []
        for index, raw_template in enumerate(raw_templates):
            if not isinstance(raw_template, Mapping):
                raise TemplateBundleError(f"template {index} must be an object")
            try:
                template_id = str(raw_template["id"])
                gloss = str(raw_template["gloss"])
                values = raw_template["values"]
            except KeyError as exc:
                raise TemplateBundleError(f"template {index} is missing a required field") from exc
            try:
                sequence = FeatureSequence.from_rows(
                    values,
                    feature_names=feature_names,
                    mask=raw_template.get("mask"),
                    timestamps_ms=raw_template.get("timestamps_ms"),
                )
            except (FeatureSequenceError, TypeError) as exc:
                raise TemplateBundleError(f"template {index} contains invalid features") from exc
            templates.append(SignTemplate(template_id, gloss, sequence))

        raw_calibration = payload.get("calibration")
        calibration = None
        if raw_calibration is not None:
            if not isinstance(raw_calibration, Mapping):
                raise TemplateBundleError("calibration must be an object")
            try:
                calibration = DistanceCalibration(
                    method=str(raw_calibration.get("method", "distance_logistic")),
                    midpoint=float(raw_calibration["midpoint"]),
                    temperature=float(raw_calibration["temperature"]),
                    validated=raw_calibration.get("validated") is True,
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise TemplateBundleError("calibration is invalid") from exc

        return cls(
            schema_version=schema_version,
            model_version=model_version,
            language=language,
            feature_names=feature_names,
            templates=tuple(templates),
            calibration=calibration,
        )

    @classmethod
    def from_json(cls, path: str | Path) -> TemplateBundle:
        try:
            with Path(path).open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise TemplateBundleError(f"could not read template bundle: {exc}") from exc
        if not isinstance(payload, Mapping):
            raise TemplateBundleError("template bundle root must be an object")
        return cls.from_dict(payload)


class DtwTemplateRecognizer:
    """Closed-vocabulary nearest-template baseline.

    Confidence is marked calibrated only when the bundle contains a calibration fitted and
    explicitly marked as validated by the data-preparation process.
    """

    def __init__(
        self,
        bundle: TemplateBundle,
        *,
        missing_penalty: float = 1.0,
        length_penalty: float = 0.1,
    ) -> None:
        if not math.isfinite(missing_penalty) or missing_penalty <= 0.0:
            raise ValueError("missing_penalty must be positive")
        if not math.isfinite(length_penalty) or length_penalty < 0.0:
            raise ValueError("length_penalty must be non-negative")
        self._bundle = bundle
        self._missing_penalty = missing_penalty
        self._length_penalty = length_penalty

    @classmethod
    def from_json(cls, path: str | Path, **kwargs: float) -> DtwTemplateRecognizer:
        return cls(TemplateBundle.from_json(path), **kwargs)

    @property
    def metadata(self) -> RecognitionMetadata:
        calibration = self._bundle.calibration
        return RecognitionMetadata(
            ready=True,
            calibrated=calibration is not None and calibration.validated,
            schema_version=self._bundle.schema_version,
            model_version=self._bundle.model_version,
            language=self._bundle.language,
            vocabulary=self._bundle.vocabulary,
            template_count=len(self._bundle.templates),
            feature_names=self._bundle.feature_names,
            calibration_method=calibration.method if calibration is not None else None,
            issues=(
                ()
                if calibration is not None and calibration.validated
                else ("confidence_calibration_unvalidated",)
            ),
        )

    def recognize(self, sequence: Any, *, top_k: int = 3) -> RecognitionResult:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        try:
            features = coerce_feature_sequence(sequence).reordered(self._bundle.feature_names)
        except (FeatureSequenceError, TypeError, ValueError) as exc:
            metadata = _metadata_with_issue(self.metadata, f"invalid_input:{exc}")
            return RecognitionResult(candidates=(), metadata=metadata)

        if features.frame_count == 0:
            return RecognitionResult(
                candidates=(),
                metadata=_metadata_with_issue(self.metadata, "empty_sequence"),
                input_coverage=features.coverage,
                frame_count=0,
                duration_ms=features.duration_ms,
            )
        if features.coverage <= 0.0:
            return RecognitionResult(
                candidates=(),
                metadata=_metadata_with_issue(self.metadata, "no_valid_features"),
                input_coverage=0.0,
                frame_count=features.frame_count,
                duration_ms=features.duration_ms,
            )

        best_by_gloss: dict[str, tuple[float, SignTemplate]] = {}
        for template in self._bundle.templates:
            distance = masked_dtw_distance(
                features,
                template.sequence,
                missing_penalty=self._missing_penalty,
                length_penalty=self._length_penalty,
            )
            current = best_by_gloss.get(template.gloss)
            if current is None or distance < current[0]:
                best_by_gloss[template.gloss] = (distance, template)

        ranked = sorted(
            best_by_gloss.items(),
            key=lambda item: (item[1][0], item[0]),
        )[: min(top_k, len(best_by_gloss))]
        candidates = tuple(
            RecognitionCandidate(
                gloss=gloss,
                confidence=self._confidence(distance),
                distance=distance,
                template_id=template.template_id,
            )
            for gloss, (distance, template) in ranked
        )
        return RecognitionResult(
            candidates=candidates,
            metadata=self.metadata,
            input_coverage=features.coverage,
            frame_count=features.frame_count,
            duration_ms=features.duration_ms,
        )

    def _confidence(self, distance: float) -> float:
        calibration = self._bundle.calibration
        if calibration is not None:
            return calibration.confidence(distance)
        # A monotonic diagnostic score is useful for debugging, but metadata explicitly
        # labels it uncalibrated so the default policy cannot accept it as speech.
        return math.exp(-distance)


def masked_dtw_distance(
    left: FeatureSequence,
    right: FeatureSequence,
    *,
    missing_penalty: float = 1.0,
    length_penalty: float = 0.1,
) -> float:
    """Compute time-normalized DTW distance over jointly valid dimensions."""

    if left.feature_names != right.feature_names:
        raise FeatureSequenceError("DTW inputs must use the same ordered feature schema")
    if not left.values or not right.values:
        return math.inf

    previous: list[tuple[float, int]] = [(math.inf, 0)] * (len(right.values) + 1)
    previous[0] = (0.0, 0)
    for left_values, left_mask in zip(left.values, left.mask, strict=True):
        current: list[tuple[float, int]] = [(math.inf, 0)] * (len(right.values) + 1)
        for column, (right_values, right_mask) in enumerate(
            zip(right.values, right.mask, strict=True), start=1
        ):
            local = _masked_frame_distance(
                left_values,
                left_mask,
                right_values,
                right_mask,
                missing_penalty=missing_penalty,
            )
            predecessor = min(
                (previous[column], current[column - 1], previous[column - 1]),
                key=lambda item: (item[0], item[1]),
            )
            current[column] = (predecessor[0] + local, predecessor[1] + 1)
        previous = current

    total, path_length = previous[-1]
    if not math.isfinite(total) or path_length == 0:
        return math.inf
    relative_length_difference = abs(len(left.values) - len(right.values)) / max(
        len(left.values), len(right.values)
    )
    return total / path_length + length_penalty * relative_length_difference


def _masked_frame_distance(
    left_values: tuple[float, ...],
    left_mask: tuple[bool, ...],
    right_values: tuple[float, ...],
    right_mask: tuple[bool, ...],
    *,
    missing_penalty: float,
) -> float:
    common = tuple(
        index
        for index, (left_valid, right_valid) in enumerate(zip(left_mask, right_mask, strict=True))
        if left_valid and right_valid
    )
    if not common:
        return missing_penalty
    squared_error = sum((left_values[index] - right_values[index]) ** 2 for index in common)
    root_mean_square = math.sqrt(squared_error / len(common))
    missing_fraction = 1.0 - len(common) / len(left_values)
    return root_mean_square + missing_penalty * missing_fraction


def _metadata_with_issue(
    metadata: RecognitionMetadata,
    issue: str,
) -> RecognitionMetadata:
    return RecognitionMetadata(
        ready=False,
        calibrated=metadata.calibrated,
        schema_version=metadata.schema_version,
        model_version=metadata.model_version,
        language=metadata.language,
        vocabulary=metadata.vocabulary,
        template_count=metadata.template_count,
        feature_names=metadata.feature_names,
        calibration_method=metadata.calibration_method,
        issues=metadata.issues + (issue,),
    )
