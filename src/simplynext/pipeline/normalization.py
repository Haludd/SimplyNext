"""Robust body-relative normalization and temporal feature extraction.

Incoming MediaPipe ``z`` is crop-relative, not metric depth. Translation, rotation,
scale, velocity, and acceleration therefore use only the image-plane ``x``/``y``
coordinates. ``relative_z`` remains available as explicitly non-metric metadata.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, pi, sin
from statistics import median

from simplynext.contracts import (
    FACE_LANDMARK_NAMES,
    HAND_LANDMARK_NAMES,
    POSE_LANDMARK_NAMES,
    LandmarkFrame,
    LandmarkPoint,
)

_GROUP_NAMES = ("pose", "left_hand", "right_hand", "face")
_GROUP_LAYOUTS: dict[str, tuple[str, ...]] = {
    "pose": tuple(POSE_LANDMARK_NAMES),
    "left_hand": tuple(HAND_LANDMARK_NAMES),
    "right_hand": tuple(HAND_LANDMARK_NAMES),
    "face": tuple(FACE_LANDMARK_NAMES),
}


class NormalizationError(ValueError):
    """Raised when a sequence has no trustworthy body reference."""


@dataclass(frozen=True, slots=True)
class NormalizationConfig:
    """Configuration for sequence-level normalization."""

    min_point_confidence: float = 0.35
    min_shoulder_width: float = 0.02
    min_reference_frames: int = 1
    max_interpolation_gap_ms: int = 160
    interpolated_confidence_factor: float = 0.5
    min_palm_scale: float = 0.005

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_point_confidence <= 1.0:
            raise ValueError("min_point_confidence must be between 0 and 1")
        if self.min_shoulder_width <= 0.0:
            raise ValueError("min_shoulder_width must be positive")
        if self.min_reference_frames < 1:
            raise ValueError("min_reference_frames must be at least 1")
        if self.max_interpolation_gap_ms < 0:
            raise ValueError("max_interpolation_gap_ms cannot be negative")
        if not 0.0 <= self.interpolated_confidence_factor <= 1.0:
            raise ValueError("interpolated_confidence_factor must be between 0 and 1")
        if self.min_palm_scale <= 0.0:
            raise ValueError("min_palm_scale must be positive")


@dataclass(frozen=True, slots=True)
class BodyReference:
    """The single robust 2D transform applied to a complete sequence."""

    center_x: float
    center_y: float
    # Diagnostic only; z remains crop-relative and is never transformed as metric depth.
    relative_z_origin: float
    shoulder_width: float
    rotation_radians: float
    supporting_frames: int


@dataclass(frozen=True, slots=True)
class NormalizedPoint:
    """One point plus an explicit observed/interpolated provenance mask."""

    x: float = 0.0
    y: float = 0.0
    relative_z: float = 0.0
    confidence: float = 0.0
    observed: bool = False
    interpolated: bool = False

    @property
    def valid(self) -> bool:
        return self.observed or self.interpolated


@dataclass(frozen=True, slots=True)
class GroupQuality:
    observed_fraction: float
    available_fraction: float
    interpolated_fraction: float
    mean_confidence: float


@dataclass(frozen=True, slots=True)
class SequenceQuality:
    """Coverage retained for confidence policy and observability."""

    observed_fraction: float
    available_fraction: float
    interpolated_fraction: float
    mean_confidence: float
    mean_tracking_confidence: float | None
    shoulder_reference_frames: int
    groups: tuple[tuple[str, GroupQuality], ...]

    def for_group(self, name: str) -> GroupQuality:
        for group_name, quality in self.groups:
            if group_name == name:
                return quality
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class NormalizedFrame:
    seq: int
    capture_ms: int
    pose: tuple[NormalizedPoint, ...]
    left_hand: tuple[NormalizedPoint, ...]
    right_hand: tuple[NormalizedPoint, ...]
    face: tuple[NormalizedPoint, ...]
    left_handshape: tuple[NormalizedPoint, ...]
    right_handshape: tuple[NormalizedPoint, ...]

    def group(self, name: str) -> tuple[NormalizedPoint, ...]:
        if name == "pose":
            return self.pose
        if name == "left_hand":
            return self.left_hand
        if name == "right_hand":
            return self.right_hand
        if name == "face":
            return self.face
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class NormalizedSequence:
    frames: tuple[NormalizedFrame, ...]
    reference: BodyReference
    quality: SequenceQuality

    def __post_init__(self) -> None:
        if not self.frames:
            raise ValueError("normalized sequence must contain at least one frame")
        timestamps = tuple(frame.capture_ms for frame in self.frames)
        if any(
            current <= previous
            for previous, current in zip(timestamps, timestamps[1:], strict=False)
        ):
            raise ValueError("normalized frame timestamps must be strictly increasing")

    @property
    def started_at_ms(self) -> int:
        return self.frames[0].capture_ms

    @property
    def ended_at_ms(self) -> int:
        return self.frames[-1].capture_ms

    @property
    def duration_ms(self) -> int:
        return self.ended_at_ms - self.started_at_ms


@dataclass(frozen=True, slots=True)
class TemporalFeatureFrame:
    capture_ms: int
    values: tuple[float, ...]
    mask: tuple[bool, ...]
    confidence: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class TemporalFeatureSequence:
    """Uniform positions and optional derivatives; normalized-z is excluded."""

    feature_names: tuple[str, ...]
    frames: tuple[TemporalFeatureFrame, ...]
    source_quality: SequenceQuality

    def __post_init__(self) -> None:
        if not self.feature_names:
            raise ValueError("feature_names must not be empty")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature_names must be unique")
        if not self.frames:
            raise ValueError("temporal feature sequence must contain at least one frame")
        width = len(self.feature_names)
        for frame in self.frames:
            if not (len(frame.values) == len(frame.mask) == len(frame.confidence) == width):
                raise ValueError("values, mask, and confidence must match the feature schema")
            if any(
                valid and not isfinite(value)
                for value, valid in zip(frame.values, frame.mask, strict=True)
            ):
                raise ValueError("valid feature values must be finite")
        if any(
            current.capture_ms <= previous.capture_ms
            for previous, current in zip(self.frames, self.frames[1:], strict=False)
        ):
            raise ValueError("temporal feature timestamps must be strictly increasing")

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.frames), len(self.feature_names))

    @property
    def values(self) -> tuple[tuple[float, ...], ...]:
        return tuple(frame.values for frame in self.frames)

    @property
    def mask(self) -> tuple[tuple[bool, ...], ...]:
        return tuple(frame.mask for frame in self.frames)

    @property
    def confidence(self) -> tuple[tuple[float, ...], ...]:
        return tuple(frame.confidence for frame in self.frames)

    @property
    def timestamps_ms(self) -> tuple[int, ...]:
        return tuple(frame.capture_ms for frame in self.frames)

    @property
    def duration_ms(self) -> int:
        return self.timestamps_ms[-1] - self.timestamps_ms[0]


@dataclass(frozen=True, slots=True)
class _RawPoint:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    confidence: float = 0.0
    observed: bool = False
    interpolated: bool = False

    @property
    def valid(self) -> bool:
        return self.observed or self.interpolated


def _index(names: Sequence[str], expected: str) -> int:
    try:
        return names.index(expected)
    except ValueError as exc:  # pragma: no cover - signals a package mismatch
        raise RuntimeError(f"landmark contract is missing {expected!r}") from exc


_LEFT_SHOULDER = _index(_GROUP_LAYOUTS["pose"], "left_shoulder")
_RIGHT_SHOULDER = _index(_GROUP_LAYOUTS["pose"], "right_shoulder")
_WRIST = _index(_GROUP_LAYOUTS["left_hand"], "wrist")


def _find_hand_index(*candidates: str, fallback: int) -> int:
    for name in candidates:
        if name in _GROUP_LAYOUTS["left_hand"]:
            return _GROUP_LAYOUTS["left_hand"].index(name)
    return fallback


_INDEX_MCP = _find_hand_index("index_finger_mcp", "index_mcp", fallback=5)
_MIDDLE_MCP = _find_hand_index("middle_finger_mcp", "middle_mcp", fallback=9)
_PINKY_MCP = _find_hand_index("pinky_mcp", "pinky_finger_mcp", fallback=17)


def _as_raw_point(point: LandmarkPoint, min_confidence: float) -> _RawPoint:
    try:
        x, y, z, confidence = point
        x, y, z, confidence = float(x), float(y), float(z), float(confidence)
    except (TypeError, ValueError):
        return _RawPoint()
    if not all(isfinite(value) for value in (x, y, z, confidence)):
        return _RawPoint()
    if confidence < min_confidence:
        return _RawPoint()
    return _RawPoint(x, y, z, confidence, observed=True)


def _landmark_group(
    frame: LandmarkFrame,
    name: str,
) -> tuple[LandmarkPoint, ...] | None:
    if name == "pose":
        return frame.pose
    if name == "left_hand":
        return frame.left_hand
    if name == "right_hand":
        return frame.right_hand
    if name == "face":
        return frame.face
    raise KeyError(name)


def _extract_groups(
    frames: Sequence[LandmarkFrame], config: NormalizationConfig
) -> dict[str, list[list[_RawPoint]]]:
    extracted: dict[str, list[list[_RawPoint]]] = {}
    for group_name, layout in _GROUP_LAYOUTS.items():
        rows: list[list[_RawPoint]] = []
        for frame in frames:
            source = _landmark_group(frame, group_name)
            if source is None:
                rows.append([_RawPoint() for _ in layout])
            else:
                if len(source) != len(layout):
                    raise NormalizationError(
                        f"{group_name} has {len(source)} points; expected {len(layout)}"
                    )
                rows.append([_as_raw_point(point, config.min_point_confidence) for point in source])
        extracted[group_name] = rows
    return extracted


def _interpolate_short_gaps(
    groups: dict[str, list[list[_RawPoint]]],
    timestamps: Sequence[int],
    config: NormalizationConfig,
) -> None:
    if config.max_interpolation_gap_ms == 0:
        return
    for group_name, layout in _GROUP_LAYOUTS.items():
        rows = groups[group_name]
        for point_index in range(len(layout)):
            cursor = 0
            while cursor < len(rows):
                if rows[cursor][point_index].valid:
                    cursor += 1
                    continue
                gap_start = cursor
                while cursor < len(rows) and not rows[cursor][point_index].valid:
                    cursor += 1
                left, right = gap_start - 1, cursor
                if left < 0 or right >= len(rows):
                    continue
                left_point = rows[left][point_index]
                right_point = rows[right][point_index]
                span_ms = timestamps[right] - timestamps[left]
                if span_ms <= 0 or span_ms > config.max_interpolation_gap_ms:
                    continue
                confidence = (
                    min(left_point.confidence, right_point.confidence)
                    * config.interpolated_confidence_factor
                )
                for missing_index in range(gap_start, right):
                    alpha = (timestamps[missing_index] - timestamps[left]) / span_ms
                    rows[missing_index][point_index] = _RawPoint(
                        x=left_point.x + alpha * (right_point.x - left_point.x),
                        y=left_point.y + alpha * (right_point.y - left_point.y),
                        z=left_point.z + alpha * (right_point.z - left_point.z),
                        confidence=confidence,
                        interpolated=True,
                    )


def _horizontal_angle(dx: float, dy: float) -> float:
    angle = atan2(dy, dx)
    if angle > pi / 2:
        angle -= pi
    elif angle < -pi / 2:
        angle += pi
    return angle


def _build_reference(
    pose_rows: Sequence[Sequence[_RawPoint]], config: NormalizationConfig
) -> BodyReference:
    centers_x: list[float] = []
    centers_y: list[float] = []
    centers_z: list[float] = []
    widths: list[float] = []
    angles: list[float] = []
    for pose in pose_rows:
        left, right = pose[_LEFT_SHOULDER], pose[_RIGHT_SHOULDER]
        if not left.valid or not right.valid:
            continue
        width = hypot(right.x - left.x, right.y - left.y)
        if width < config.min_shoulder_width:
            continue
        centers_x.append((left.x + right.x) / 2.0)
        centers_y.append((left.y + right.y) / 2.0)
        centers_z.append((left.z + right.z) / 2.0)
        widths.append(width)
        angles.append(_horizontal_angle(right.x - left.x, right.y - left.y))
    if len(widths) < config.min_reference_frames:
        raise NormalizationError(
            "sequence does not contain enough confident, separated shoulder pairs"
        )
    return BodyReference(
        center_x=median(centers_x),
        center_y=median(centers_y),
        relative_z_origin=median(centers_z),
        shoulder_width=median(widths),
        rotation_radians=median(angles),
        supporting_frames=len(widths),
    )


def _normalize_point(point: _RawPoint, reference: BodyReference) -> NormalizedPoint:
    if not point.valid:
        return NormalizedPoint()
    dx, dy = point.x - reference.center_x, point.y - reference.center_y
    rotation = -reference.rotation_radians
    rotated_x = dx * cos(rotation) - dy * sin(rotation)
    rotated_y = dx * sin(rotation) + dy * cos(rotation)
    return NormalizedPoint(
        x=rotated_x / reference.shoulder_width,
        y=rotated_y / reference.shoulder_width,
        # Preserve as-is. Hand, face, and pose z may use different crop-relative origins.
        relative_z=point.z,
        confidence=point.confidence,
        observed=point.observed,
        interpolated=point.interpolated,
    )


def _palm_scale(points: Sequence[NormalizedPoint], minimum: float) -> float | None:
    wrist = points[_WRIST]
    if not wrist.valid:
        return None
    distances: list[float] = []
    for index in (_INDEX_MCP, _MIDDLE_MCP, _PINKY_MCP):
        if index < len(points) and points[index].valid:
            distance = hypot(points[index].x - wrist.x, points[index].y - wrist.y)
            if distance >= minimum:
                distances.append(distance)
    return median(distances) if distances else None


def _handshape(
    points: Sequence[NormalizedPoint], config: NormalizationConfig
) -> tuple[NormalizedPoint, ...]:
    scale = _palm_scale(points, config.min_palm_scale)
    wrist = points[_WRIST]
    if scale is None or not wrist.valid:
        return tuple(NormalizedPoint() for _ in points)
    shaped: list[NormalizedPoint] = []
    for point in points:
        if not point.valid:
            shaped.append(NormalizedPoint())
        else:
            shaped.append(
                NormalizedPoint(
                    x=(point.x - wrist.x) / scale,
                    y=(point.y - wrist.y) / scale,
                    # Orientation/depth ordering retained without 2D palm scaling.
                    relative_z=point.relative_z - wrist.relative_z,
                    confidence=min(point.confidence, wrist.confidence),
                    observed=point.observed and wrist.observed,
                    interpolated=point.interpolated or wrist.interpolated,
                )
            )
    return tuple(shaped)


def _group_quality(rows: Sequence[Sequence[_RawPoint]]) -> GroupQuality:
    points = [point for row in rows for point in row]
    if not points:
        return GroupQuality(0.0, 0.0, 0.0, 0.0)
    observed = [point for point in points if point.observed]
    available = [point for point in points if point.valid]
    interpolated = [point for point in points if point.interpolated]
    return GroupQuality(
        observed_fraction=len(observed) / len(points),
        available_fraction=len(available) / len(points),
        interpolated_fraction=len(interpolated) / len(points),
        mean_confidence=(
            sum(point.confidence for point in observed) / len(observed) if observed else 0.0
        ),
    )


def _sequence_quality(
    frames: Sequence[LandmarkFrame],
    groups: dict[str, list[list[_RawPoint]]],
    reference: BodyReference,
) -> SequenceQuality:
    group_items = tuple(
        (group_name, _group_quality(groups[group_name])) for group_name in _GROUP_NAMES
    )
    all_points = [point for name in _GROUP_NAMES for row in groups[name] for point in row]
    observed = [point for point in all_points if point.observed]
    available = [point for point in all_points if point.valid]
    interpolated = [point for point in all_points if point.interpolated]
    tracking = [
        float(frame.tracking_confidence)
        for frame in frames
        if frame.tracking_confidence is not None
    ]
    return SequenceQuality(
        observed_fraction=len(observed) / len(all_points),
        available_fraction=len(available) / len(all_points),
        interpolated_fraction=len(interpolated) / len(all_points),
        mean_confidence=(
            sum(point.confidence for point in observed) / len(observed) if observed else 0.0
        ),
        mean_tracking_confidence=sum(tracking) / len(tracking) if tracking else None,
        shoulder_reference_frames=reference.supporting_frames,
        groups=group_items,
    )


class SequenceNormalizer:
    """Normalize complete utterance windows using one robust body transform."""

    def __init__(self, config: NormalizationConfig | None = None) -> None:
        self.config = config or NormalizationConfig()

    def normalize(self, frames: Sequence[LandmarkFrame]) -> NormalizedSequence:
        frame_tuple = tuple(frames)
        if not frame_tuple:
            raise NormalizationError("cannot normalize an empty sequence")
        timestamps = tuple(frame.capture_ms for frame in frame_tuple)
        if any(
            current <= previous
            for previous, current in zip(timestamps, timestamps[1:], strict=False)
        ):
            raise NormalizationError("capture_ms must be strictly increasing")

        groups = _extract_groups(frame_tuple, self.config)
        _interpolate_short_gaps(groups, timestamps, self.config)
        reference = _build_reference(groups["pose"], self.config)
        normalized_frames: list[NormalizedFrame] = []
        for frame_index, frame in enumerate(frame_tuple):
            normalized = {
                name: tuple(
                    _normalize_point(point, reference) for point in groups[name][frame_index]
                )
                for name in _GROUP_NAMES
            }
            normalized_frames.append(
                NormalizedFrame(
                    seq=frame.seq,
                    capture_ms=frame.capture_ms,
                    pose=normalized["pose"],
                    left_hand=normalized["left_hand"],
                    right_hand=normalized["right_hand"],
                    face=normalized["face"],
                    left_handshape=_handshape(normalized["left_hand"], self.config),
                    right_handshape=_handshape(normalized["right_hand"], self.config),
                )
            )
        return NormalizedSequence(
            frames=tuple(normalized_frames),
            reference=reference,
            quality=_sequence_quality(frame_tuple, groups, reference),
        )


def normalize_sequence(
    frames: Sequence[LandmarkFrame], config: NormalizationConfig | None = None
) -> NormalizedSequence:
    return SequenceNormalizer(config).normalize(frames)


def _position_schema() -> tuple[tuple[str, str, int], ...]:
    schema: list[tuple[str, str, int]] = []
    for group_name in _GROUP_NAMES:
        for point_index, landmark_name in enumerate(_GROUP_LAYOUTS[group_name]):
            schema.append((group_name, landmark_name, point_index))
    for group_name in ("left_handshape", "right_handshape"):
        for point_index, landmark_name in enumerate(HAND_LANDMARK_NAMES):
            schema.append((group_name, landmark_name, point_index))
    return tuple(schema)


_POSITION_SCHEMA = _position_schema()
_POSITION_FEATURE_NAMES = tuple(
    f"{group}.{landmark}.{axis}" for group, landmark, _ in _POSITION_SCHEMA for axis in ("x", "y")
)


def temporal_feature_names(
    *,
    include_velocity: bool = True,
    include_acceleration: bool = True,
) -> tuple[str, ...]:
    """Return the exact feature schema emitted by :func:`resample_sequence`."""

    if include_acceleration and not include_velocity:
        raise ValueError("acceleration requires velocity")
    names = list(_POSITION_FEATURE_NAMES)
    if include_velocity:
        names.extend(f"{name}.velocity" for name in _POSITION_FEATURE_NAMES)
    if include_acceleration:
        names.extend(f"{name}.acceleration" for name in _POSITION_FEATURE_NAMES)
    return tuple(names)


def _flatten_positions(
    frame: NormalizedFrame,
) -> tuple[list[float], list[bool], list[float]]:
    values: list[float] = []
    masks: list[bool] = []
    confidence: list[float] = []
    for group_name, _, point_index in _POSITION_SCHEMA:
        point = getattr(frame, group_name)[point_index]
        for value in (point.x, point.y):
            values.append(value if point.valid else 0.0)
            masks.append(point.valid)
            confidence.append(point.confidence if point.valid else 0.0)
    return values, masks, confidence


def _resample_positions(
    sequence: NormalizedSequence, target_frames: int, max_gap_ms: int
) -> tuple[list[int], list[list[float]], list[list[bool]], list[list[float]]]:
    if target_frames < 1:
        raise ValueError("target_frames must be at least 1")
    source_times = [frame.capture_ms for frame in sequence.frames]
    flattened = [_flatten_positions(frame) for frame in sequence.frames]
    dimension = len(_POSITION_FEATURE_NAMES)
    if target_frames == 1:
        target_times = [source_times[0]]
    else:
        if len(source_times) < 2:
            raise ValueError("target_frames greater than 1 requires at least two source frames")
        duration = source_times[-1] - source_times[0]
        if duration < target_frames - 1:
            raise ValueError(
                "capture duration is too short for distinct millisecond resample timestamps"
            )
        target_times = [
            round(source_times[0] + duration * index / (target_frames - 1))
            for index in range(target_frames)
        ]

    output_values: list[list[float]] = []
    output_masks: list[list[bool]] = []
    output_confidence: list[list[float]] = []
    source_right = 0
    for target in target_times:
        while source_right < len(source_times) and source_times[source_right] < target:
            source_right += 1
        if source_right < len(source_times) and source_times[source_right] == target:
            values, masks, confidence = flattened[source_right]
            output_values.append(list(values))
            output_masks.append(list(masks))
            output_confidence.append(list(confidence))
            continue
        left, right = source_right - 1, source_right
        if left < 0 or right >= len(source_times):  # defensive round-off fallback
            nearest = max(0, min(source_right, len(source_times) - 1))
            values, masks, confidence = flattened[nearest]
            output_values.append(list(values))
            output_masks.append(list(masks))
            output_confidence.append(list(confidence))
            continue
        span = source_times[right] - source_times[left]
        alpha = (target - source_times[left]) / span
        left_values, left_masks, left_confidence = flattened[left]
        right_values, right_masks, right_confidence = flattened[right]
        values = [0.0] * dimension
        masks = [False] * dimension
        confidence = [0.0] * dimension
        if span <= max_gap_ms:
            for feature_index in range(dimension):
                if left_masks[feature_index] and right_masks[feature_index]:
                    values[feature_index] = left_values[feature_index] + alpha * (
                        right_values[feature_index] - left_values[feature_index]
                    )
                    masks[feature_index] = True
                    confidence[feature_index] = min(
                        left_confidence[feature_index], right_confidence[feature_index]
                    )
        output_values.append(values)
        output_masks.append(masks)
        output_confidence.append(confidence)
    return target_times, output_values, output_masks, output_confidence


def _differentiate(
    values: Sequence[Sequence[float]],
    masks: Sequence[Sequence[bool]],
    times: Sequence[int],
) -> tuple[list[list[float]], list[list[bool]]]:
    frame_count = len(values)
    dimension = len(values[0]) if values else 0
    derivative = [[0.0] * dimension for _ in range(frame_count)]
    derivative_masks = [[False] * dimension for _ in range(frame_count)]
    if frame_count < 2:
        return derivative, derivative_masks
    for frame_index in range(frame_count):
        if frame_index == 0:
            left, right = 0, 1
        elif frame_index == frame_count - 1:
            left, right = frame_count - 2, frame_count - 1
        else:
            left, right = frame_index - 1, frame_index + 1
        elapsed_seconds = (times[right] - times[left]) / 1000.0
        if elapsed_seconds <= 0:
            continue
        for feature_index in range(dimension):
            if masks[left][feature_index] and masks[right][feature_index]:
                derivative[frame_index][feature_index] = (
                    values[right][feature_index] - values[left][feature_index]
                ) / elapsed_seconds
                derivative_masks[frame_index][feature_index] = True
    return derivative, derivative_masks


def resample_sequence(
    sequence: NormalizedSequence,
    target_frames: int = 32,
    *,
    max_gap_ms: int = 250,
    include_velocity: bool = True,
    include_acceleration: bool = True,
) -> TemporalFeatureSequence:
    """Uniformly resample a sequence without bridging long tracking gaps."""

    if not sequence.frames:
        raise ValueError("cannot resample an empty normalized sequence")
    if max_gap_ms < 0:
        raise ValueError("max_gap_ms cannot be negative")
    if include_acceleration and not include_velocity:
        raise ValueError("acceleration requires velocity")
    times, positions, position_masks, position_confidence = _resample_positions(
        sequence, target_frames, max_gap_ms
    )
    velocities, velocity_masks = _differentiate(positions, position_masks, times)
    accelerations, acceleration_masks = _differentiate(velocities, velocity_masks, times)
    names = temporal_feature_names(
        include_velocity=include_velocity,
        include_acceleration=include_acceleration,
    )

    frames: list[TemporalFeatureFrame] = []
    dimension = len(_POSITION_FEATURE_NAMES)
    for frame_index, capture_ms in enumerate(times):
        values = list(positions[frame_index])
        masks = list(position_masks[frame_index])
        confidence = list(position_confidence[frame_index])
        if include_velocity:
            values.extend(velocities[frame_index])
            masks.extend(velocity_masks[frame_index])
            confidence.extend(
                position_confidence[frame_index][i] if velocity_masks[frame_index][i] else 0.0
                for i in range(dimension)
            )
        if include_acceleration:
            values.extend(accelerations[frame_index])
            masks.extend(acceleration_masks[frame_index])
            confidence.extend(
                position_confidence[frame_index][i] if acceleration_masks[frame_index][i] else 0.0
                for i in range(dimension)
            )
        frames.append(
            TemporalFeatureFrame(capture_ms, tuple(values), tuple(masks), tuple(confidence))
        )
    return TemporalFeatureSequence(names, tuple(frames), sequence.quality)


def iter_valid_points(points: Iterable[NormalizedPoint]) -> Iterable[NormalizedPoint]:
    """Yield valid points for simple baselines and diagnostics."""

    return (point for point in points if point.valid)
