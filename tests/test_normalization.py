from __future__ import annotations

from math import cos, sin

import pytest

from simplynext.contracts import (
    FACE_LANDMARK_NAMES,
    HAND_LANDMARK_NAMES,
    POSE_LANDMARK_NAMES,
    LandmarkFrame,
)
from simplynext.pipeline.normalization import (
    NormalizationConfig,
    NormalizationError,
    normalize_sequence,
    resample_sequence,
)

Point = tuple[float, float, float, float]


def _point(x: float, y: float, z: float = 0.0, confidence: float = 0.95) -> Point:
    return (x, y, z, confidence)


def _pose(
    *,
    center_x: float = 0.5,
    center_y: float = 0.4,
    width: float = 0.2,
    left_wrist_x: float = 0.40,
    left_wrist_y: float = 0.45,
) -> tuple[Point, ...]:
    locations = {
        "nose": (center_x, center_y - 0.22),
        "left_shoulder": (center_x - width / 2.0, center_y),
        "right_shoulder": (center_x + width / 2.0, center_y),
        "left_elbow": (center_x - width * 0.65, center_y + width * 0.6),
        "right_elbow": (center_x + width * 0.65, center_y + width * 0.6),
        "left_wrist": (left_wrist_x, left_wrist_y),
        "right_wrist": (center_x + width * 0.65, center_y + width * 0.25),
        "left_hip": (center_x - width * 0.4, center_y + width * 1.6),
        "right_hip": (center_x + width * 0.4, center_y + width * 1.6),
    }
    return tuple(_point(*locations[name], z=0.1) for name in POSE_LANDMARK_NAMES)


def _hand(
    wrist_x: float,
    wrist_y: float,
    *,
    missing: set[int] | None = None,
) -> tuple[Point, ...]:
    missing = missing or set()
    points: list[Point] = []
    for index, _name in enumerate(HAND_LANDMARK_NAMES):
        if index in missing:
            points.append(_point(0.0, 0.0, confidence=0.0))
        elif index == 0:
            points.append(_point(wrist_x, wrist_y, z=-0.02))
        else:
            finger = (index - 1) // 4
            joint = (index - 1) % 4 + 1
            points.append(
                _point(
                    wrist_x + (finger - 2) * 0.012,
                    wrist_y - joint * 0.018,
                    z=-0.02 - joint * 0.002,
                )
            )
    return tuple(points)


def _face(center_x: float = 0.5, center_y: float = 0.24) -> tuple[Point, ...]:
    return tuple(
        _point(center_x + (index % 4 - 1.5) * 0.01, center_y + (index // 4) * 0.01)
        for index in range(len(FACE_LANDMARK_NAMES))
    )


def _frame(
    seq: int,
    capture_ms: int,
    *,
    center_x: float = 0.5,
    center_y: float = 0.4,
    width: float = 0.2,
    hand_x: float = 0.4,
    hand_y: float = 0.45,
    missing_hand_points: set[int] | None = None,
) -> LandmarkFrame:
    return LandmarkFrame(
        seq=seq,
        capture_ms=capture_ms,
        pose=_pose(
            center_x=center_x,
            center_y=center_y,
            width=width,
            left_wrist_x=hand_x,
            left_wrist_y=hand_y,
        ),
        left_hand=_hand(hand_x, hand_y, missing=missing_hand_points),
        right_hand=None,
        face=_face(center_x, center_y - 0.16),
        left_hand_score=0.95,
        tracking_confidence=0.9,
    )


def _transform_group(
    group: tuple[Point, ...] | None,
    *,
    scale: float,
    angle: float,
    translate_x: float,
    translate_y: float,
    translate_z: float,
) -> tuple[Point, ...] | None:
    if group is None:
        return None
    transformed = []
    for x, y, z, confidence in group:
        transformed.append(
            _point(
                scale * (x * cos(angle) - y * sin(angle)) + translate_x,
                scale * (x * sin(angle) + y * cos(angle)) + translate_y,
                z + translate_z,
                confidence,
            )
        )
    return tuple(transformed)


def _transform_frame(frame: LandmarkFrame) -> LandmarkFrame:
    kwargs = {
        "scale": 1.7,
        "angle": 0.21,
        "translate_x": 0.8,
        "translate_y": -0.35,
        # Crop-relative z does not participate in the global camera transform.
        "translate_z": 0.0,
    }
    return LandmarkFrame(
        seq=frame.seq,
        capture_ms=frame.capture_ms,
        pose=_transform_group(frame.pose, **kwargs),
        left_hand=_transform_group(frame.left_hand, **kwargs),
        right_hand=_transform_group(frame.right_hand, **kwargs),
        face=_transform_group(frame.face, **kwargs),
        left_hand_score=frame.left_hand_score,
        tracking_confidence=frame.tracking_confidence,
    )


def test_normalization_is_translation_scale_and_rotation_invariant() -> None:
    source = tuple(_frame(i, i * 100, hand_x=0.36 + i * 0.015) for i in range(5))
    transformed = tuple(_transform_frame(frame) for frame in source)

    normalized = normalize_sequence(source)
    normalized_transformed = normalize_sequence(transformed)

    for original_frame, transformed_frame in zip(
        normalized.frames, normalized_transformed.frames, strict=True
    ):
        for group_name in ("pose", "left_hand", "face", "left_handshape"):
            for original, changed in zip(
                getattr(original_frame, group_name),
                getattr(transformed_frame, group_name),
                strict=True,
            ):
                assert changed.x == pytest.approx(original.x, abs=1e-9)
                assert changed.y == pytest.approx(original.y, abs=1e-9)
                assert changed.relative_z == pytest.approx(original.relative_z, abs=1e-9)


def test_reference_uses_medians_and_ignores_one_shoulder_outlier() -> None:
    frames = (
        _frame(0, 0, center_x=0.50, width=0.200),
        _frame(1, 100, center_x=0.501, width=0.202),
        _frame(2, 200, center_x=3.00, center_y=-2.0, width=1.400),
        _frame(3, 300, center_x=0.499, width=0.198),
        _frame(4, 400, center_x=0.50, width=0.200),
    )

    result = normalize_sequence(frames)

    assert result.reference.center_x == pytest.approx(0.5)
    assert result.reference.center_y == pytest.approx(0.4)
    assert result.reference.shoulder_width == pytest.approx(0.2)
    assert result.reference.supporting_frames == 5


def test_short_internal_gap_is_interpolated_but_remains_auditable() -> None:
    index_tip = HAND_LANDMARK_NAMES.index("index_tip")
    frames = (
        _frame(0, 0, hand_x=0.36),
        _frame(1, 100, hand_x=0.38, missing_hand_points={index_tip}),
        _frame(2, 200, hand_x=0.40),
    )

    result = normalize_sequence(frames, NormalizationConfig(max_interpolation_gap_ms=250))
    before = result.frames[0].left_hand[index_tip]
    middle = result.frames[1].left_hand[index_tip]
    after = result.frames[2].left_hand[index_tip]

    assert middle.valid
    assert middle.interpolated
    assert not middle.observed
    assert middle.x == pytest.approx((before.x + after.x) / 2.0)
    assert middle.confidence < before.confidence
    assert result.quality.for_group("left_hand").interpolated_fraction > 0.0


def test_long_gap_is_not_interpolated() -> None:
    index_tip = HAND_LANDMARK_NAMES.index("index_tip")
    frames = (
        _frame(0, 0, hand_x=0.36),
        _frame(1, 500, hand_x=0.38, missing_hand_points={index_tip}),
        _frame(2, 1_000, hand_x=0.40),
    )

    result = normalize_sequence(frames, NormalizationConfig(max_interpolation_gap_ms=200))

    assert not result.frames[1].left_hand[index_tip].valid


def test_resampling_has_stable_masks_and_xy_derivatives_only() -> None:
    frames = tuple(_frame(i, i * 100, hand_x=0.36 + i * 0.02) for i in range(3))
    normalized = normalize_sequence(frames)

    features = resample_sequence(normalized, target_frames=5)

    assert features.shape == (5, len(features.feature_names))
    assert features.timestamps_ms == (0, 50, 100, 150, 200)
    assert all(len(row) == len(features.feature_names) for row in features.values)
    assert all(len(row) == len(features.feature_names) for row in features.mask)
    assert not any("z" in name.rsplit(".", 1)[-1] for name in features.feature_names)
    wrist_x = features.feature_names.index("left_hand.wrist.x")
    wrist_velocity = features.feature_names.index("left_hand.wrist.x.velocity")
    wrist_acceleration = features.feature_names.index("left_hand.wrist.x.acceleration")
    assert [row[wrist_x] for row in features.values] == pytest.approx(
        [-0.7, -0.65, -0.6, -0.55, -0.5]
    )
    assert [row[wrist_velocity] for row in features.values] == pytest.approx([1.0] * 5)
    assert [row[wrist_acceleration] for row in features.values] == pytest.approx([0.0] * 5)


def test_sequence_without_shoulders_fails_closed() -> None:
    frame = LandmarkFrame(seq=0, capture_ms=0, pose=None, left_hand=_hand(0.4, 0.4))

    with pytest.raises(NormalizationError, match="shoulder"):
        normalize_sequence((frame,))


def test_timestamps_must_be_strictly_increasing() -> None:
    with pytest.raises(NormalizationError, match="strictly increasing"):
        normalize_sequence((_frame(0, 100), _frame(1, 100)))


def test_resampling_does_not_invent_a_timeline_from_one_capture() -> None:
    normalized = normalize_sequence((_frame(0, 100),))

    with pytest.raises(ValueError, match="at least two source frames"):
        resample_sequence(normalized, target_frames=2)
