"""Closed-vocabulary temporal recognition and fail-closed confidence policy."""

from .dtw import (
    BUNDLE_SCHEMA_VERSION,
    DistanceCalibration,
    DtwTemplateRecognizer,
    SignTemplate,
    TemplateBundle,
    TemplateBundleError,
    masked_dtw_distance,
)
from .policy import (
    ConfidencePolicy,
    ConfidenceThresholds,
    DecisionStatus,
    PolicyDecision,
    RecognitionQuality,
    RepairAction,
)
from .recognizer import Recognizer, UnconfiguredRecognizer
from .types import (
    FeatureSequence,
    FeatureSequenceError,
    RecognitionCandidate,
    RecognitionMetadata,
    RecognitionResult,
    coerce_feature_sequence,
)

__all__ = [
    "BUNDLE_SCHEMA_VERSION",
    "ConfidencePolicy",
    "ConfidenceThresholds",
    "DecisionStatus",
    "DistanceCalibration",
    "DtwTemplateRecognizer",
    "FeatureSequence",
    "FeatureSequenceError",
    "PolicyDecision",
    "RecognitionCandidate",
    "RecognitionMetadata",
    "RecognitionQuality",
    "RecognitionResult",
    "Recognizer",
    "RepairAction",
    "SignTemplate",
    "TemplateBundle",
    "TemplateBundleError",
    "UnconfiguredRecognizer",
    "coerce_feature_sequence",
    "masked_dtw_distance",
]
