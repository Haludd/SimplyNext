#!/usr/bin/env python3
"""Run the checked-in synthetic landmark stream through the existing engine."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.signbridge_backend.analyzer import SignAnalyzer  # noqa: E402
from backend.signbridge_backend.models import SignSequencePayload  # noqa: E402


def open_hand(x: float, y: float) -> list[dict[str, float]]:
    """Return a simple synthetic 21-point open hand around the wrist."""
    relative = [
        (0.00, 0.00), (-0.03, -0.01), (-0.05, -0.03), (-0.08, -0.02), (-0.10, -0.01),
        (0.02, -0.07), (0.02, -0.11), (0.02, -0.14), (0.02, -0.18),
        (0.00, -0.07), (0.00, -0.10), (0.00, -0.12), (0.00, -0.16),
        (-0.02, -0.06), (-0.02, -0.08), (-0.02, -0.10), (-0.02, -0.13),
        (-0.04, -0.05), (-0.04, -0.06), (-0.04, -0.065), (-0.04, -0.07),
    ]
    return [{"x": x + dx, "y": y + dy, "z": 0.0} for dx, dy in relative]


def add_stage3_normalization(frame: dict) -> None:
    """Add the same shoulder-centred 3D shape emitted by Flutter stage 3."""
    origin = {"x": 0.5, "y": 0.45, "z": 0.0}
    shoulder_width = 0.30
    normalized_hands = []
    for hand in frame["hands"]:
        normalized_hands.append({
            "handedness": hand["handedness"],
            "confidence": hand["confidence"],
            "landmarks": [
                {
                    "x": round((point["x"] - origin["x"]) / shoulder_width, 6),
                    "y": round((point["y"] - origin["y"]) / shoulder_width, 6),
                    "z": round((point["z"] - origin["z"]) / shoulder_width, 6),
                    "confidence": round(hand["confidence"], 6),
                }
                for point in hand["landmarks"]
            ],
        })
    frame["normalized_coordinates"] = normalized_hands
    frame["normalization"] = {
        "coordinate_space": "shoulder_centered_normalized_3d",
        "origin": origin,
        "scale": shoulder_width,
        "confidence": 0.95,
        "source": "stage_3_body_normalization",
    }


def build_payload(source: dict) -> SignSequencePayload:
    start = datetime(2026, 9, 6, 8, 14, tzinfo=timezone.utc)
    frames = []
    for index, position in enumerate(source["wrist_positions"]):
        timestamp = (start + timedelta(seconds=index / 10)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        frame = {
            "timestamp": timestamp,
            "tracking_confidence": 0.98,
            "hands": [{
                "handedness": "right",
                "confidence": 0.96,
                "landmarks": open_hand(position["x"], position["y"]),
            }],
            "left_shoulder": {"x": 0.35, "y": 0.45, "z": 0.0, "visibility": 0.95},
            "right_shoulder": {"x": 0.65, "y": 0.45, "z": 0.0, "visibility": 0.95},
            "left_hip": {"x": 0.40, "y": 0.90, "z": 0.0, "visibility": 0.95},
            "right_hip": {"x": 0.60, "y": 0.90, "z": 0.0, "visibility": 0.95},
        }
        add_stage3_normalization(frame)
        frames.append(frame)
    value = {
        "session_id": source["session_id"],
        "sequence_id": source["sequence_id"],
        "language": source["language"],
        "started_at": frames[0]["timestamp"],
        "ended_at": frames[-1]["timestamp"],
        "frame_count": len(frames),
        "lexicon_version": source["lexicon_version"],
        "frames": frames,
    }
    return SignSequencePayload.from_dict(value)


def run(arm: str) -> None:
    source = json.loads((Path(__file__).with_name("sample_positions.json")).read_text())
    result = SignAnalyzer(segmenter_arm=arm).analyze(build_payload(source))
    print(f"\nSEGMENTER ARM: {arm}")
    print(f"frames: {source['wrist_positions'].__len__()}")
    print(f"phrases/windows: {result['segmentation']['phrase_count']}")
    print(f"boundary events: {len(result['boundary_events'])}")
    first_window = result["feature_windows"][0] if result["feature_windows"] else None
    if first_window and first_window["normalized_coordinates"]:
        first_hand = first_window["normalized_coordinates"][0]["hands"][0]
        print("stage-3 normalized wrist:", first_hand["landmarks"][0])
    for phrase in result["segmentation"]["phrases"]:
        print(
            f"  {phrase['phrase_id']}: frames {phrase['start_index']}..{phrase['end_index']} "
            f"({phrase['boundary_before']} -> {phrase['boundary_after']})"
        )
    print("top-k candidate:", json.dumps(result["top_k_glosses"], indent=2))
    print("NOTE: this is synthetic wiring data; it is not a trained ASL recognizer.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arm",
        choices=("both", "geometry_hysteresis", "sliding_window_blank"),
        default="both",
    )
    args = parser.parse_args()
    arms = ("geometry_hysteresis", "sliding_window_blank") if args.arm == "both" else (args.arm,)
    for arm in arms:
        run(arm)


if __name__ == "__main__":
    main()
