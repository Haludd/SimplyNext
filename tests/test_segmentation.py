from __future__ import annotations

import pytest

from simplynext.contracts import HAND_LANDMARK_NAMES, POSE_LANDMARK_NAMES, LandmarkFrame
from simplynext.pipeline.segmentation import (
    SegmenterConfig,
    SegmenterState,
    SegmentEventType,
    SegmentReason,
    UtteranceSegmenter,
    measure_activity,
)

Point = tuple[float, float, float, float]


def _point(x: float, y: float, confidence: float = 0.95) -> Point:
    return (x, y, 0.0, confidence)


def _hand(x: float, y: float) -> tuple[Point, ...]:
    return tuple(
        _point(x + (index % 4) * 0.002, y - (index // 4) * 0.002)
        for index in range(len(HAND_LANDMARK_NAMES))
    )


def _pose(
    center_x: float,
    *,
    hand_x: float,
    hand_y: float,
    hands_visible: bool,
) -> tuple[Point, ...]:
    confidence = 0.95 if hands_visible else 0.0
    positions: dict[str, Point] = {
        "nose": _point(center_x, 0.20),
        "left_shoulder": _point(center_x - 0.10, 0.40),
        "right_shoulder": _point(center_x + 0.10, 0.40),
        "left_elbow": _point(center_x - 0.12, 0.52),
        "right_elbow": _point(center_x + 0.12, 0.52),
        "left_wrist": _point(hand_x, hand_y, confidence),
        "right_wrist": _point(center_x + 0.13, hand_y, confidence),
        "left_hip": _point(center_x - 0.08, 0.72),
        "right_hip": _point(center_x + 0.08, 0.72),
    }
    return tuple(positions[name] for name in POSE_LANDMARK_NAMES)


def _frame(
    seq: int,
    capture_ms: int,
    hand_x: float,
    *,
    hand_y: float = 0.36,
    center_x: float = 0.5,
    hands_visible: bool = True,
) -> LandmarkFrame:
    return LandmarkFrame(
        seq=seq,
        capture_ms=capture_ms,
        pose=_pose(
            center_x,
            hand_x=hand_x,
            hand_y=hand_y,
            hands_visible=hands_visible,
        ),
        left_hand=_hand(hand_x, hand_y) if hands_visible else None,
        tracking_confidence=0.95,
    )


def _config(**changes: object) -> SegmenterConfig:
    defaults: dict[str, object] = {
        "start_evidence_frames": 2,
        "stop_evidence_frames": 2,
        "pre_roll_ms": 250,
        "inactivity_ms": 200,
        "missing_hands_timeout_ms": 300,
        "min_utterance_ms": 100,
        "max_utterance_ms": 2_000,
        "start_motion_units_per_second": 0.1,
        "continue_motion_units_per_second": 0.05,
    }
    defaults.update(changes)
    return SegmenterConfig(**defaults)


def test_hysteresis_replays_bounded_preroll_and_discards_end_pause() -> None:
    segmenter = UtteranceSegmenter(_config())
    frames = (
        _frame(0, 0, 0.30),
        _frame(1, 100, 0.30),
        _frame(2, 200, 0.36),
        _frame(3, 300, 0.40),
        _frame(4, 400, 0.44),
        _frame(5, 500, 0.44),
        _frame(6, 600, 0.44),
    )

    events = [
        event for frame in frames for event in segmenter.process(frame, subject_id="signer-a")
    ]

    assert [event.type for event in events] == [
        SegmentEventType.STARTED,
        SegmentEventType.COMMITTED,
    ]
    committed = events[-1]
    assert committed.reason == SegmentReason.INACTIVITY
    # Frame zero is outside the 250 ms pre-roll at the 300 ms onset commit.
    assert [frame.seq for frame in committed.frames] == [1, 2, 3, 4]
    # The two end-evidence frames are not passed to the classifier.
    assert 5 not in [frame.seq for frame in committed.frames]
    assert 6 not in [frame.seq for frame in committed.frames]
    assert segmenter.state == SegmenterState.IDLE


def test_possible_end_frames_are_replayed_when_motion_resumes() -> None:
    segmenter = UtteranceSegmenter(_config())
    frames = (
        _frame(0, 0, 0.30),
        _frame(1, 100, 0.36),
        _frame(2, 200, 0.40),
        _frame(3, 300, 0.40),  # possible end
        _frame(4, 400, 0.46),  # resumes; frame 3 must be replayed
        _frame(5, 500, 0.46),
        _frame(6, 600, 0.46),
    )
    events = [event for frame in frames for event in segmenter.process(frame)]

    committed = next(event for event in events if event.type == SegmentEventType.COMMITTED)

    assert 3 in [frame.seq for frame in committed.frames]
    assert [frame.seq for frame in committed.frames][-1] == 4


def test_short_candidate_is_discarded_instead_of_classified() -> None:
    segmenter = UtteranceSegmenter(
        _config(
            start_evidence_frames=1,
            stop_evidence_frames=1,
            inactivity_ms=100,
            min_utterance_ms=500,
        )
    )
    frames = (
        _frame(0, 0, 0.30),
        _frame(1, 100, 0.36),
        _frame(2, 200, 0.36),
    )

    events = [event for frame in frames for event in segmenter.process(frame)]

    assert events[-1].type == SegmentEventType.DISCARDED
    assert events[-1].reason == SegmentReason.TOO_SHORT


def test_maximum_duration_forces_a_commit() -> None:
    segmenter = UtteranceSegmenter(
        _config(start_evidence_frames=1, max_utterance_ms=200, min_utterance_ms=0)
    )
    frames = (
        _frame(0, 0, 0.30),
        _frame(1, 100, 0.34),
        _frame(2, 200, 0.38),
        _frame(3, 300, 0.42),
    )

    events = [event for frame in frames for event in segmenter.process(frame)]

    assert events[-1].type == SegmentEventType.COMMITTED
    assert events[-1].reason == SegmentReason.MAX_DURATION


def test_manual_force_commit_bypasses_hysteresis_and_minimum_duration() -> None:
    segmenter = UtteranceSegmenter(
        _config(
            start_evidence_frames=3,
            min_utterance_ms=5_000,
            max_utterance_ms=6_000,
        )
    )
    segmenter.process(_frame(0, 0, 0.30))
    segmenter.process(_frame(1, 100, 0.36))
    assert segmenter.state == SegmenterState.POSSIBLE_START

    event = segmenter.force_commit()

    assert event is not None
    assert event.type == SegmentEventType.COMMITTED
    assert event.reason == SegmentReason.MANUAL_COMMIT
    assert [frame.seq for frame in event.frames] == [0, 1]


def test_subject_change_resets_instead_of_splicing_signers() -> None:
    segmenter = UtteranceSegmenter(_config(start_evidence_frames=1))
    segmenter.process(_frame(0, 0, 0.30), subject_id="signer-a")
    segmenter.process(_frame(1, 100, 0.36), subject_id="signer-a")
    assert segmenter.state == SegmenterState.ACTIVE

    events = segmenter.process(_frame(2, 200, 0.60), subject_id="signer-b")

    assert events[0].type == SegmentEventType.RESET
    assert events[0].reason == SegmentReason.SUBJECT_CHANGED
    assert events[0].subject_id == "signer-a"
    assert segmenter.subject_id == "signer-b"
    assert segmenter.state == SegmenterState.IDLE


def test_missing_hands_timeout_commits_existing_activity() -> None:
    segmenter = UtteranceSegmenter(
        _config(
            start_evidence_frames=1,
            stop_evidence_frames=1,
            inactivity_ms=10_000,
            missing_hands_timeout_ms=200,
            min_utterance_ms=0,
        )
    )
    frames = (
        _frame(0, 0, 0.30),
        _frame(1, 100, 0.36),
        _frame(2, 200, 0.36, hands_visible=False),
        _frame(3, 300, 0.36, hands_visible=False),
    )

    events = [event for frame in frames for event in segmenter.process(frame)]

    assert events[-1].type == SegmentEventType.COMMITTED
    assert events[-1].reason == SegmentReason.MISSING_HANDS


def test_body_translation_does_not_count_as_hand_motion() -> None:
    before = _frame(0, 0, 0.35, center_x=0.50)
    after = _frame(1, 100, 0.55, center_x=0.70)

    activity = measure_activity(after, before, config=_config())

    assert activity.motion_units_per_second == pytest.approx(0.0, abs=1e-12)
    assert not activity.start_active


def test_out_of_order_timestamp_is_rejected() -> None:
    segmenter = UtteranceSegmenter(_config())
    segmenter.process(_frame(0, 100, 0.30))

    with pytest.raises(ValueError, match="strictly increasing"):
        segmenter.process(_frame(1, 100, 0.32))
