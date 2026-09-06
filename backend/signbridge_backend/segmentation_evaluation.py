"""Small evaluation harness for comparing stage-④ segmentation arms."""

from __future__ import annotations

from typing import Any, Iterable

from .segmentation import PhraseSegment, create_segmenter


def predicted_boundaries(segments: Iterable[PhraseSegment]) -> list[int]:
    return sorted({segment.end_index for segment in segments})


def boundary_scores(
    predicted: Iterable[int],
    reference: Iterable[int],
    *,
    tolerance_frames: int = 2,
) -> dict[str, float | int]:
    """Score boundary agreement with one-to-one tolerance matching."""
    candidates = sorted(set(int(value) for value in predicted))
    expected = sorted(set(int(value) for value in reference))
    matched: set[int] = set()
    true_positive = 0
    for candidate in candidates:
        match = next(
            (
                index for index, target in enumerate(expected)
                if index not in matched and abs(candidate - target) <= tolerance_frames
            ),
            None,
        )
        if match is not None:
            matched.add(match)
            true_positive += 1
    precision = true_positive / len(candidates) if candidates else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "predicted": len(candidates),
        "reference": len(expected),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "tolerance_frames": tolerance_frames,
    }


def compare_arms(
    frames: list[dict[str, Any]],
    reference_boundaries: Iterable[int],
    *,
    tolerance_frames: int = 2,
) -> dict[str, Any]:
    """Run both stage-④ arms against the same held-out boundary labels."""
    reference = list(reference_boundaries)
    report: dict[str, Any] = {"reference_boundaries": reference, "arms": {}}
    for arm in ("geometry_hysteresis", "sliding_window_blank"):
        segmenter = create_segmenter(arm)
        segments = segmenter.segment(frames)
        report["arms"][arm] = {
            "segment_count": len(segments),
            "boundaries": predicted_boundaries(segments),
            "scores": boundary_scores(
                predicted_boundaries(segments),
                reference,
                tolerance_frames=tolerance_frames,
            ),
        }
    return report
