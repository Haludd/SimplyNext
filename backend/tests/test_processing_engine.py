from __future__ import annotations

import json
from pathlib import Path
import unittest

from backend.signbridge_backend.analyzer import SignAnalyzer
from backend.signbridge_backend.classifier_features import (
    ClassifierFeatureEngine,
    FeatureAssemblyConfig,
)
from backend.signbridge_backend.models import SignSequencePayload
from backend.signbridge_backend.processing_contracts import LandmarkFrame
from backend.signbridge_backend.segmentation import (
    PhraseSegmenter,
    SlidingWindowSegmenter,
)
from backend.signbridge_backend.segmentation_evaluation import (
    boundary_scores,
    compare_arms,
)
from backend.signbridge_backend.temporal_classifier import TemporalPrototypeClassifier


def hand_shape(shape: str, x: float, y: float) -> list[dict[str, float]]:
    """Small synthetic 21-point hand used to exercise geometric proposals."""
    points = [
        (0.00, 0.00),  # wrist
        (-0.03, -0.01),
        (-0.05, -0.03),  # thumb CMC/MCP
        (-0.08, -0.02),
        (-0.10, -0.01),  # thumb tip
        (0.02, -0.07),  # index MCP
        (0.02, -0.11),
        (0.02, -0.14),
        (0.02, -0.18),  # index tip
        (0.00, -0.07),  # middle MCP
        (0.00, -0.10),
        (0.00, -0.12),
        (0.00, -0.16),  # middle tip
        (-0.02, -0.06),  # ring MCP
        (-0.02, -0.08),
        (-0.02, -0.10),
        (-0.02, -0.13),  # ring tip
        (-0.04, -0.05),  # pinky MCP
        (-0.04, -0.06),
        (-0.04, -0.065),
        (-0.04, -0.07),  # pinky tip
    ]
    if shape == "1":
        for index in (12, 16, 20):
            points[index] = (points[index][0], -0.045)
        points[4] = (-0.04, -0.015)
    elif shape == "3":
        points[20] = (-0.04, -0.045)
        points[4] = (-0.04, -0.015)
    elif shape == "C":
        points = [
            (0.00, 0.00), (-0.04, -0.01), (-0.07, -0.03), (-0.09, -0.04), (-0.10, -0.05),
            (0.03, -0.06), (0.05, -0.10), (0.06, -0.13), (0.05, -0.16),
            (0.01, -0.07), (0.03, -0.11), (0.04, -0.14), (0.03, -0.17),
            (-0.02, -0.06), (-0.01, -0.10), (0.00, -0.13), (-0.01, -0.16),
            (-0.05, -0.04), (-0.04, -0.08), (-0.03, -0.11), (-0.04, -0.14),
        ]
    return [
        {"x": x + point[0], "y": y + point[1], "z": 0.0}
        for point in points
    ]


def frame(index: int, x: float, y: float, *, shape: str = "1", **extra) -> dict:
    return {
        "timestamp": f"2026-09-05T08:14:{index:02d}.000Z",
        "tracking_confidence": 0.95,
        "hands": [{
            "handedness": "right",
            "confidence": 0.92,
            "landmarks": hand_shape(shape, x, y),
        }],
        "left_shoulder": {"x": 0.35, "y": 0.45, "z": 0.0, "visibility": 0.9},
        "right_shoulder": {"x": 0.65, "y": 0.45, "z": 0.0, "visibility": 0.9},
        **extra,
    }


class ProcessingEngineTests(unittest.TestCase):
    def test_landmark_frame_groups_confidence_and_running_averages(self) -> None:
        first = frame(0, 0.3, 0.5)
        second = frame(1, 0.4, 0.5)
        second["tracking_confidence"] = 0.85
        second["hands"][0]["confidence"] = 0.8
        typed = LandmarkFrame.from_sequence([first, second])
        self.assertEqual(typed[0].landmark_groups["hands"][0]["handedness"], "right")
        self.assertTrue(typed[0].group_presence["shoulders"])
        self.assertEqual(typed[0].normalization["coordinate_space"], "image_normalized")
        self.assertEqual(typed[1].running_averages["tracking_confidence"], 0.9)
        self.assertEqual(typed[1].running_averages["hands"]["right"], 0.86)
        self.assertIn("running_averages", typed[1].to_dict())

    def test_processing_schema_declares_all_three_stage_handoffs(self) -> None:
        schema_path = (
            Path(__file__).parents[2]
            / "frontend_segment_classify"
            / "schema"
            / "processing_contracts.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        landmark_frame = schema["$defs"]["landmarkFrame"]
        self.assertIn("timestamp", landmark_frame["required"])
        self.assertIn("tracking_confidence", landmark_frame["properties"])
        self.assertNotIn("schema_version", landmark_frame["properties"])
        self.assertIn("landmarkFrameStage3", schema["$defs"])
        self.assertIn("landmarkFrameStage4", schema["$defs"])
        self.assertIn("featureWindow", schema["$defs"])
        self.assertIn("glossLattice", schema["$defs"])

    def test_segments_active_bursts_after_a_rest_pause(self) -> None:
        frames = [
            frame(0, 0.30, 0.50),
            frame(1, 0.36, 0.50),
            frame(2, 0.42, 0.50),
            frame(3, 0.42, 0.50),
            frame(4, 0.42, 0.50),
            frame(5, 0.42, 0.50),
            frame(6, 0.42, 0.50),
            frame(7, 0.42, 0.50),
            frame(8, 0.42, 0.50),
            frame(9, 0.48, 0.50),
            frame(10, 0.54, 0.50),
        ]
        segments = PhraseSegmenter().segment(frames)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].boundary_after, "rest_pause")
        self.assertEqual(segments[1].boundary_before, "rest_pause")

    def test_segmenter_accepts_typed_landmark_frames_and_replays_run_up(self) -> None:
        source = [
            frame(0, 0.30, 0.50),
            frame(1, 0.30, 0.50),
            frame(2, 0.42, 0.50),
        ]
        typed = [LandmarkFrame.from_dict(value, index) for index, value in enumerate(source)]
        segments = PhraseSegmenter().segment(typed)
        self.assertEqual(segments[0].start_index, 0)
        self.assertEqual(segments[0].segmenter_arm, "geometry_hysteresis")

    def test_classifier_proposes_representative_handshapes(self) -> None:
        engine = ClassifierFeatureEngine()
        for expected in ("1_HANDSHAPE", "3_HANDSHAPE", "C_HANDSHAPE"):
            source_shape = expected[0]
            features = engine.extract([frame(0, 0.5, 0.5, shape=source_shape)])
            self.assertEqual(features["classifier_handshape"], expected)

    def test_feature_assembly_is_configurable_and_fixed_width(self) -> None:
        config = FeatureAssemblyConfig(hand_landmark_indices=(0, 8, 12))
        engine = ClassifierFeatureEngine(config)
        features = engine.extract([frame(0, 0.5, 0.5)])
        self.assertEqual(features["feature_dimension"], config.feature_dimension)
        self.assertEqual(len(features["feature_sequence"][0]), config.feature_dimension)
        self.assertEqual(len(config.schema()["hand_landmark_indices"]), 3)

    def test_sliding_window_arm_uses_the_same_segment_contract(self) -> None:
        frames = [frame(index, 0.35 + index * 0.01, 0.5) for index in range(20)]
        segments = SlidingWindowSegmenter().segment(frames)
        self.assertEqual(segments[0].segmenter_arm, "sliding_window_blank")
        self.assertEqual(segments[0].end_index - segments[0].start_index + 1, 16)
        self.assertTrue(any(
            event.event_type == "utterance_boundary"
            for event in segments[-1].boundary_events or []
        ))

    def test_temporal_classifier_trains_calibrates_and_can_refuse(self) -> None:
        classifier = TemporalPrototypeClassifier(refusal_threshold=0.6)
        classifier.fit([
            ("HELLO", [[0.0, 0.0], [0.1, 0.0]]),
            ("GOODBYE", [[1.0, 1.0], [0.9, 1.0]]),
        ])
        classifier.calibrate([
            ("HELLO", [[0.0, 0.0], [0.1, 0.0]]),
            ("GOODBYE", [[1.0, 1.0], [0.9, 1.0]]),
        ])
        result = classifier.predict([[0.0, 0.0], [0.1, 0.0]])
        self.assertEqual(result["top_k_glosses"][0]["gloss"], "HELLO")
        self.assertTrue(result["calibrated"])
        self.assertIn("HELLO", result["class_scores"])

    def test_boundary_scores_are_one_to_one_and_tolerant(self) -> None:
        result = boundary_scores([10, 30, 31], [11, 50], tolerance_frames=1)
        self.assertEqual(result["true_positive"], 1)
        self.assertEqual(result["predicted"], 3)
        self.assertEqual(result["reference"], 2)

    def test_comparison_harness_runs_both_segmentation_arms(self) -> None:
        frames = [frame(index, 0.35 + index * 0.01, 0.5) for index in range(20)]
        report = compare_arms(frames, [15, 19])
        self.assertEqual(
            set(report["arms"]),
            {"geometry_hysteresis", "sliding_window_blank"},
        )

    def test_extracts_trajectory_space_anchor_and_non_manual_markers(self) -> None:
        frames = [
            frame(0, 0.30, 0.50, gloss="CAR"),
            frame(1, 0.42, 0.42),
            frame(2, 0.30, 0.34),
            frame(3, 0.42, 0.26),
            frame(4, 0.30, 0.18),
            frame(5, 0.42, 0.10),
        ]
        for item in frames:
            item["face_expression"] = {
                "head_roll": -0.2,
                "blendshapes": {"browInnerUp": 0.7},
            }
        features = ClassifierFeatureEngine().extract(frames)
        self.assertEqual(features["anchor_noun"], "CAR")
        self.assertEqual(features["trajectory"], "ZIGZAG")
        self.assertEqual(features["non_manual_markers"]["brow_state"], "RAISED")
        self.assertEqual(features["non_manual_markers"]["head_tilt"], "LEFT")
        self.assertEqual(features["spatial_mapping"]["coordinate_space"], "shoulder_centered_normalized_3d")

    def test_analyzer_returns_segmentation_and_classifier_tokens(self) -> None:
        frames = [frame(0, 0.45, 0.5, shape="3", fingerspelled="CAR")]
        value = {
            "session_id": "session-engine",
            "sequence_id": "sequence-engine",
            "language": "ASL",
            "started_at": frames[0]["timestamp"],
            "ended_at": frames[-1]["timestamp"],
            "frame_count": len(frames),
            "lexicon_version": "test",
            "frames": frames,
        }
        result = SignAnalyzer().analyze(SignSequencePayload.from_dict(value))
        self.assertEqual(result["segmentation"]["phrase_count"], 1)
        self.assertEqual(result["classifier_phrases"][0]["anchor_noun"], "CAR")
        self.assertIn("classifier_handshape", result["classifier_phrases"][0])
        self.assertEqual(len(result["feature_windows"]), 1)
        window = result["feature_windows"][0]
        self.assertEqual(window["frame_range"], {"start": 0, "end": 0})
        self.assertEqual(window["segmenter_arm"], "geometry_hysteresis")
        self.assertIn("normalized_coordinates", window)
        self.assertIn("velocity", window)
        self.assertIn("acceleration", window)
        self.assertTrue(any(
            event["event_type"] == "utterance_boundary"
            for event in result["boundary_events"]
        ))
        self.assertEqual(result["top_k_glosses"][0]["gloss"], "3_HANDSHAPE")
        self.assertIn("3_HANDSHAPE", result["class_scores"])
        self.assertEqual(result["gloss_lattice"][0]["slot"], "phrase_001")
        self.assertNotIn("normalized_coordinates", result["gloss_lattice"][0])
        lattice = result["gloss_lattice_message"]
        self.assertEqual(lattice["type"], "gloss_lattice")
        self.assertEqual(lattice["schema_version"], "1.0")
        self.assertEqual(lattice["producer"]["segmenter_arm"], "geometry_hysteresis")
        self.assertIn("gloss_id", lattice["slots"][0]["candidates"][0])
        self.assertNotIn("normalized_coordinates", json.dumps(lattice))


if __name__ == "__main__":
    unittest.main()
