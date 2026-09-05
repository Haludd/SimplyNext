from __future__ import annotations

import json

import pytest

from simplynext.config import Settings
from simplynext.observability import MetricsRegistry
from simplynext.orchestrator import build_translation_engine
from simplynext.recognition import (
    DtwTemplateRecognizer,
    FeatureSequence,
    Recognizer,
    TemplateBundle,
    TemplateBundleError,
    UnconfiguredRecognizer,
    masked_dtw_distance,
)


def _bundle_payload(*, validated: bool = True) -> dict[str, object]:
    return {
        "schema_version": 1,
        "model_version": "demo-dtw-v1",
        "language": "asl",
        "feature_names": ["wrist.x", "wrist.y"],
        "calibration": {
            "method": "distance_logistic",
            "midpoint": 2.0,
            "temperature": 0.5,
            "validated": validated,
        },
        "templates": [
            {
                "id": "hello-a",
                "gloss": "HELLO",
                "values": [[0.0, 0.0], [1.0, 1.0]],
            },
            {
                "id": "hello-b",
                "gloss": "HELLO",
                "values": [[0.1, 0.0], [1.1, 1.0]],
            },
            {
                "id": "bye-a",
                "gloss": "BYE",
                "values": [[10.0, 10.0], [11.0, 11.0]],
            },
        ],
    }


def test_unconfigured_recognizer_conforms_and_never_guesses() -> None:
    recognizer = UnconfiguredRecognizer()

    assert isinstance(recognizer, Recognizer)
    result = recognizer.recognize(object())

    assert result.candidates == ()
    assert result.metadata.ready is False
    assert result.metadata.issues == ("recognizer_unconfigured",)


def test_template_bundle_loads_from_versioned_json_and_returns_distinct_top_k(
    tmp_path,
) -> None:
    path = tmp_path / "templates.json"
    path.write_text(json.dumps(_bundle_payload()), encoding="utf-8")
    recognizer = DtwTemplateRecognizer.from_json(path)
    sequence = FeatureSequence.from_rows(
        [[0.0, None], [1.0, None]],
        feature_names=("wrist.x", "wrist.y"),
        timestamps_ms=(1_000, 1_500),
    )

    result = recognizer.recognize(sequence, top_k=3)

    assert [candidate.gloss for candidate in result.candidates] == ["HELLO", "BYE"]
    assert result.candidates[0].template_id == "hello-a"
    assert result.candidates[0].confidence > result.candidates[1].confidence
    assert result.metadata.ready is True
    assert result.metadata.calibrated is True
    assert result.metadata.model_version == "demo-dtw-v1"
    assert result.metadata.template_count == 3
    assert result.input_coverage == pytest.approx(0.5)
    assert result.duration_ms == 500


def test_recognizer_reorders_same_named_features() -> None:
    recognizer = DtwTemplateRecognizer(TemplateBundle.from_dict(_bundle_payload()))
    pipeline_shaped_value = {
        "feature_names": ("wrist.y", "wrist.x"),
        "values": ((0.0, 0.0), (1.0, 1.0)),
        "mask": ((True, True), (True, True)),
        "timestamps_ms": (0, 300),
    }

    result = recognizer.recognize(pipeline_shaped_value)

    assert result.top_candidate is not None
    assert result.top_candidate.gloss == "HELLO"


def test_recognizer_refuses_schema_drift_instead_of_guessing() -> None:
    recognizer = DtwTemplateRecognizer(TemplateBundle.from_dict(_bundle_payload()))

    result = recognizer.recognize(
        {
            "feature_names": ("unknown.x",),
            "values": ((0.0,),),
            "mask": ((True,),),
        }
    )

    assert result.candidates == ()
    assert result.metadata.ready is False
    assert any(issue.startswith("invalid_input:") for issue in result.metadata.issues)


def test_unvalidated_calibration_is_visible_in_metadata() -> None:
    recognizer = DtwTemplateRecognizer(TemplateBundle.from_dict(_bundle_payload(validated=False)))

    assert recognizer.metadata.ready is True
    assert recognizer.metadata.calibrated is False
    assert "confidence_calibration_unvalidated" in recognizer.metadata.issues


def test_template_bundle_rejects_unknown_schema_version() -> None:
    payload = _bundle_payload()
    payload["schema_version"] = 2

    with pytest.raises(TemplateBundleError, match="unsupported bundle schema_version"):
        TemplateBundle.from_dict(payload)


def test_engine_rejects_bundle_with_wrong_pipeline_feature_schema(tmp_path) -> None:
    path = tmp_path / "wrong-schema.json"
    path.write_text(json.dumps(_bundle_payload()), encoding="utf-8")

    engine = build_translation_engine(
        Settings(template_bundle_path=path),
        MetricsRegistry(),
    )

    assert engine.recognizer.metadata.ready is False
    assert engine.recognizer.metadata.issues == ("recognizer_bundle_invalid",)


def test_masked_dtw_is_zero_for_identical_complete_sequences() -> None:
    sequence = FeatureSequence.from_rows(
        [[0.0, 1.0], [1.0, 2.0]],
        feature_names=("x", "y"),
    )

    assert masked_dtw_distance(sequence, sequence) == pytest.approx(0.0)
