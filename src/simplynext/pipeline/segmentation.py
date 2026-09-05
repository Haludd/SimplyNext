"""Deterministic geometry-and-hysteresis utterance segmentation.

The segmenter owns temporal state but knows nothing about cameras, networks, models,
or language.  It buffers uncertain onset frames and replays them after the onset is
confirmed; uncertain end frames are replayed only when motion resumes.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import hypot, isfinite, sqrt
from statistics import median

from simplynext.contracts import HAND_LANDMARK_NAMES, POSE_LANDMARK_NAMES, LandmarkFrame


def _index(names: Sequence[str], expected: str) -> int:
    try:
        return names.index(expected)
    except ValueError as exc:  # pragma: no cover - signals a package mismatch
        raise RuntimeError(f"landmark contract is missing {expected!r}") from exc


_POSE_NAMES = tuple(POSE_LANDMARK_NAMES)
_HAND_NAMES = tuple(HAND_LANDMARK_NAMES)
_NOSE = _index(_POSE_NAMES, "nose")
_LEFT_SHOULDER = _index(_POSE_NAMES, "left_shoulder")
_RIGHT_SHOULDER = _index(_POSE_NAMES, "right_shoulder")
_LEFT_ELBOW = _index(_POSE_NAMES, "left_elbow")
_RIGHT_ELBOW = _index(_POSE_NAMES, "right_elbow")
_LEFT_WRIST = _index(_POSE_NAMES, "left_wrist")
_RIGHT_WRIST = _index(_POSE_NAMES, "right_wrist")
_LEFT_HIP = _index(_POSE_NAMES, "left_hip")
_RIGHT_HIP = _index(_POSE_NAMES, "right_hip")
_HAND_WRIST = _index(_HAND_NAMES, "wrist")


class SegmenterState(StrEnum):
    IDLE = "idle"
    POSSIBLE_START = "possible_start"
    ACTIVE = "active"
    POSSIBLE_END = "possible_end"


class SegmentEventType(StrEnum):
    STARTED = "started"
    COMMITTED = "committed"
    DISCARDED = "discarded"
    RESET = "reset"


class SegmentReason(StrEnum):
    ACTIVITY = "activity"
    INACTIVITY = "inactivity"
    MISSING_HANDS = "missing_hands"
    MAX_DURATION = "max_duration"
    BUFFER_LIMIT = "buffer_limit"
    MANUAL_COMMIT = "manual_commit"
    MANUAL_RESET = "manual_reset"
    SUBJECT_CHANGED = "subject_changed"
    TOO_SHORT = "too_short"


@dataclass(frozen=True, slots=True)
class SegmenterConfig:
    min_point_confidence: float = 0.35
    start_evidence_frames: int = 3
    stop_evidence_frames: int = 3
    pre_roll_ms: int = 250
    inactivity_ms: int = 400
    missing_hands_timeout_ms: int = 650
    min_utterance_ms: int = 250
    max_utterance_ms: int = 6_000
    max_buffered_frames: int = 600
    start_motion_units_per_second: float = 0.20
    continue_motion_units_per_second: float = 0.08
    horizontal_margin_shoulders: float = 0.80
    top_margin_shoulders: float = 0.75
    bottom_margin_shoulders: float = 0.35
    shoulder_history_frames: int = 15

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_point_confidence <= 1.0:
            raise ValueError("min_point_confidence must be between 0 and 1")
        for name in ("start_evidence_frames", "stop_evidence_frames", "max_buffered_frames"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")
        for name in (
            "pre_roll_ms",
            "inactivity_ms",
            "missing_hands_timeout_ms",
            "min_utterance_ms",
            "max_utterance_ms",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.max_utterance_ms < self.min_utterance_ms:
            raise ValueError("max_utterance_ms must not be smaller than min_utterance_ms")
        if self.start_motion_units_per_second < 0.0:
            raise ValueError("start motion threshold cannot be negative")
        if not 0.0 <= self.continue_motion_units_per_second <= self.start_motion_units_per_second:
            raise ValueError("continue motion threshold must be between zero and start threshold")
        if self.shoulder_history_frames < 1:
            raise ValueError("shoulder_history_frames must be at least 1")


@dataclass(frozen=True, slots=True)
class ActivityMeasurement:
    capture_ms: int
    hands_visible: bool
    hands_in_signing_space: bool
    hands_above_rest: bool
    motion_units_per_second: float
    landmark_coverage: float
    start_active: bool
    continue_active: bool


@dataclass(frozen=True, slots=True)
class SegmentEvent:
    type: SegmentEventType
    reason: SegmentReason
    capture_ms: int
    frames: tuple[LandmarkFrame, ...] = ()
    subject_id: str | None = None

    @property
    def duration_ms(self) -> int:
        if len(self.frames) < 2:
            return 0
        return self.frames[-1].capture_ms - self.frames[0].capture_ms


def _point(group: object, index: int, confidence: float) -> tuple[float, float] | None:
    if group is None:
        return None
    try:
        x, y, _z, score = group[index]  # type: ignore[index]
        x, y, score = float(x), float(y), float(score)
    except (IndexError, TypeError, ValueError):
        return None
    if not all(isfinite(value) for value in (x, y, score)) or score < confidence:
        return None
    return (x, y)


def _body_reference(frame: LandmarkFrame, confidence: float) -> tuple[float, float, float] | None:
    left = _point(frame.pose, _LEFT_SHOULDER, confidence)
    right = _point(frame.pose, _RIGHT_SHOULDER, confidence)
    if left is None or right is None:
        return None
    width = hypot(right[0] - left[0], right[1] - left[1])
    if width <= 1e-6:
        return None
    return ((left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0, width)


def _wrists(frame: LandmarkFrame, confidence: float) -> tuple[tuple[float, float], ...]:
    wrists: list[tuple[float, float]] = []
    left = _point(frame.left_hand, _HAND_WRIST, confidence)
    right = _point(frame.right_hand, _HAND_WRIST, confidence)
    if left is None:
        left = _point(frame.pose, _LEFT_WRIST, confidence)
    if right is None:
        right = _point(frame.pose, _RIGHT_WRIST, confidence)
    if left is not None:
        wrists.append(left)
    if right is not None:
        wrists.append(right)
    return tuple(wrists)


def _motion_energy(
    frame: LandmarkFrame,
    previous: LandmarkFrame | None,
    reference_width: float,
    confidence: float,
) -> float:
    if previous is None:
        return 0.0
    elapsed_seconds = (frame.capture_ms - previous.capture_ms) / 1000.0
    if elapsed_seconds <= 0.0:
        return 0.0
    current_body = _body_reference(frame, confidence)
    previous_body = _body_reference(previous, confidence)
    if current_body is None or previous_body is None:
        return 0.0
    displacements: list[float] = []
    for group_name, fallback_index in (
        ("left_hand", _LEFT_WRIST),
        ("right_hand", _RIGHT_WRIST),
    ):
        current_group = getattr(frame, group_name)
        previous_group = getattr(previous, group_name)
        if current_group is not None and previous_group is not None:
            for point_index in range(min(len(current_group), len(previous_group))):
                current_point = _point(current_group, point_index, confidence)
                previous_point = _point(previous_group, point_index, confidence)
                if current_point is not None and previous_point is not None:
                    current_x = current_point[0] - current_body[0]
                    current_y = current_point[1] - current_body[1]
                    previous_x = previous_point[0] - previous_body[0]
                    previous_y = previous_point[1] - previous_body[1]
                    displacements.append(hypot(current_x - previous_x, current_y - previous_y))
        else:
            current_point = _point(frame.pose, fallback_index, confidence)
            previous_point = _point(previous.pose, fallback_index, confidence)
            if current_point is not None and previous_point is not None:
                displacements.append(
                    hypot(
                        (current_point[0] - current_body[0])
                        - (previous_point[0] - previous_body[0]),
                        (current_point[1] - current_body[1])
                        - (previous_point[1] - previous_body[1]),
                    )
                )
    if not displacements:
        return 0.0
    root_mean_square = sqrt(sum(value * value for value in displacements) / len(displacements))
    return root_mean_square / reference_width / elapsed_seconds


def measure_activity(
    frame: LandmarkFrame,
    previous: LandmarkFrame | None = None,
    *,
    reference_width: float | None = None,
    config: SegmenterConfig | None = None,
) -> ActivityMeasurement:
    """Measure signer-relative activity without retaining temporal state."""

    settings = config or SegmenterConfig()
    body = _body_reference(frame, settings.min_point_confidence)
    wrists = _wrists(frame, settings.min_point_confidence)
    hands_visible = bool(wrists)
    if body is None:
        return ActivityMeasurement(
            frame.capture_ms, hands_visible, False, False, 0.0, 0.0, False, False
        )
    center_x, center_y, current_width = body
    width = reference_width if reference_width and reference_width > 1e-6 else current_width
    left_shoulder = _point(frame.pose, _LEFT_SHOULDER, settings.min_point_confidence)
    right_shoulder = _point(frame.pose, _RIGHT_SHOULDER, settings.min_point_confidence)
    nose = _point(frame.pose, _NOSE, settings.min_point_confidence)
    left_hip = _point(frame.pose, _LEFT_HIP, settings.min_point_confidence)
    right_hip = _point(frame.pose, _RIGHT_HIP, settings.min_point_confidence)
    assert left_shoulder is not None and right_shoulder is not None
    minimum_x = (
        min(left_shoulder[0], right_shoulder[0]) - settings.horizontal_margin_shoulders * width
    )
    maximum_x = (
        max(left_shoulder[0], right_shoulder[0]) + settings.horizontal_margin_shoulders * width
    )
    shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
    top = shoulder_y - settings.top_margin_shoulders * width
    if nose is not None:
        top = min(top, nose[1] - 0.20 * width)
    if left_hip is not None and right_hip is not None:
        bottom = (left_hip[1] + right_hip[1]) / 2.0 + settings.bottom_margin_shoulders * width
    else:
        bottom = center_y + 2.0 * width
    in_space = any(minimum_x <= x <= maximum_x and top <= y <= bottom for x, y in wrists)

    elevated = False
    for wrist_index, elbow_index in ((_LEFT_WRIST, _LEFT_ELBOW), (_RIGHT_WRIST, _RIGHT_ELBOW)):
        wrist = _point(frame.pose, wrist_index, settings.min_point_confidence)
        elbow = _point(frame.pose, elbow_index, settings.min_point_confidence)
        if wrist is not None and elbow is not None and wrist[1] <= elbow[1] + 0.05 * width:
            elevated = True
    motion = _motion_energy(frame, previous, width, settings.min_point_confidence)

    present_hand_points = 0
    expected_hand_points = len(_HAND_NAMES) * 2
    for group in (frame.left_hand, frame.right_hand):
        if group is not None:
            present_hand_points += sum(
                _point(group, index, settings.min_point_confidence) is not None
                for index in range(min(len(group), len(_HAND_NAMES)))
            )
    coverage = present_hand_points / expected_hand_points if expected_hand_points else 0.0
    return ActivityMeasurement(
        capture_ms=frame.capture_ms,
        hands_visible=hands_visible,
        hands_in_signing_space=in_space,
        hands_above_rest=elevated,
        motion_units_per_second=motion,
        landmark_coverage=coverage,
        start_active=in_space and motion >= settings.start_motion_units_per_second,
        continue_active=in_space and motion >= settings.continue_motion_units_per_second,
    )


class UtteranceSegmenter:
    """Incremental utterance state machine with bounded buffers."""

    def __init__(self, config: SegmenterConfig | None = None) -> None:
        self.config = config or SegmenterConfig()
        self._pre_roll: deque[LandmarkFrame] = deque()
        self._shoulder_widths: deque[float] = deque(maxlen=self.config.shoulder_history_frames)
        self._active_frames: list[LandmarkFrame] = []
        self._possible_end: list[LandmarkFrame] = []
        self._state = SegmenterState.IDLE
        self._start_evidence = 0
        self._stop_evidence = 0
        self._candidate_start_ms: int | None = None
        self._last_motion_ms: int | None = None
        self._last_hands_ms: int | None = None
        self._last_capture_ms: int | None = None
        self._previous_frame: LandmarkFrame | None = None
        self._subject_id: str | None = None

    @property
    def state(self) -> SegmenterState:
        return self._state

    @property
    def subject_id(self) -> str | None:
        return self._subject_id

    @property
    def buffered_frame_count(self) -> int:
        return len(self._pre_roll) + len(self._active_frames) + len(self._possible_end)

    def process(
        self, frame: LandmarkFrame, *, subject_id: str | None = None
    ) -> tuple[SegmentEvent, ...]:
        """Consume one frame and return zero or more state-transition events."""

        events: list[SegmentEvent] = []
        if subject_id is not None:
            if self._subject_id is not None and subject_id != self._subject_id:
                event = self.reset(SegmentReason.SUBJECT_CHANGED)
                if event is not None:
                    events.append(event)
            self._subject_id = subject_id
        if self._last_capture_ms is not None and frame.capture_ms <= self._last_capture_ms:
            raise ValueError("capture_ms must be strictly increasing within a subject stream")

        body = _body_reference(frame, self.config.min_point_confidence)
        if body is not None:
            self._shoulder_widths.append(body[2])
        reference_width = median(self._shoulder_widths) if self._shoulder_widths else None
        measurement = measure_activity(
            frame,
            self._previous_frame,
            reference_width=reference_width,
            config=self.config,
        )
        self._last_capture_ms = frame.capture_ms
        self._previous_frame = frame
        if measurement.hands_visible:
            self._last_hands_ms = frame.capture_ms

        if self._state in (SegmenterState.IDLE, SegmenterState.POSSIBLE_START):
            self._append_pre_roll(frame)
            if measurement.start_active:
                if self._start_evidence == 0:
                    self._candidate_start_ms = frame.capture_ms
                self._start_evidence += 1
                self._state = SegmenterState.POSSIBLE_START
                if self._start_evidence >= self.config.start_evidence_frames:
                    self._active_frames = list(self._pre_roll)
                    self._pre_roll.clear()
                    self._state = SegmenterState.ACTIVE
                    self._last_motion_ms = frame.capture_ms
                    self._stop_evidence = 0
                    events.append(
                        SegmentEvent(
                            SegmentEventType.STARTED,
                            SegmentReason.ACTIVITY,
                            frame.capture_ms,
                            tuple(self._active_frames),
                            self._subject_id,
                        )
                    )
            else:
                self._state = SegmenterState.IDLE
                self._start_evidence = 0
                self._candidate_start_ms = None
            return tuple(events)

        if measurement.continue_active:
            if self._possible_end:
                self._active_frames.extend(self._possible_end)
                self._possible_end.clear()
            self._active_frames.append(frame)
            self._state = SegmenterState.ACTIVE
            self._stop_evidence = 0
            self._last_motion_ms = frame.capture_ms
        else:
            self._possible_end.append(frame)
            self._state = SegmenterState.POSSIBLE_END
            self._stop_evidence += 1

        active_origin = self._candidate_start_ms or self._active_frames[0].capture_ms
        active_duration = frame.capture_ms - active_origin
        if active_duration >= self.config.max_utterance_ms:
            event = self._finish(SegmentReason.MAX_DURATION, frame.capture_ms)
            if event is not None:
                events.append(event)
            return tuple(events)
        if len(self._active_frames) + len(self._possible_end) >= self.config.max_buffered_frames:
            event = self._finish(SegmentReason.BUFFER_LIMIT, frame.capture_ms)
            if event is not None:
                events.append(event)
            return tuple(events)

        inactive_long_enough = (
            self._last_motion_ms is not None
            and frame.capture_ms - self._last_motion_ms >= self.config.inactivity_ms
        )
        hands_missing_long_enough = (
            self._last_hands_ms is not None
            and not measurement.hands_visible
            and frame.capture_ms - self._last_hands_ms >= self.config.missing_hands_timeout_ms
        )
        if self._stop_evidence >= self.config.stop_evidence_frames and (
            inactive_long_enough or hands_missing_long_enough
        ):
            reason = (
                SegmentReason.MISSING_HANDS
                if hands_missing_long_enough
                else SegmentReason.INACTIVITY
            )
            event = self._finish(reason, frame.capture_ms)
            if event is not None:
                events.append(event)
        return tuple(events)

    def force_commit(self) -> SegmentEvent | None:
        """Commit currently buffered activity, bypassing minimum duration."""

        if self._state in (SegmenterState.IDLE,) and not self._start_evidence:
            return None
        if not self._active_frames:
            self._active_frames = list(self._pre_roll)
            self._pre_roll.clear()
        capture_ms = self._last_capture_ms or 0
        return self._finish(SegmentReason.MANUAL_COMMIT, capture_ms, enforce_minimum=False)

    def reset(self, reason: SegmentReason = SegmentReason.MANUAL_RESET) -> SegmentEvent | None:
        """Discard all candidate data; subject changes must use this path."""

        subject_id = self._subject_id
        if self._active_frames:
            frames = tuple((*self._active_frames, *self._possible_end))
        else:
            frames = tuple(self._pre_roll)
        capture_ms = self._last_capture_ms or 0
        had_state = self._state != SegmenterState.IDLE or bool(frames) or bool(self._start_evidence)
        self._clear_detection(keep_temporal=False)
        self._subject_id = None
        if not had_state:
            return None
        return SegmentEvent(SegmentEventType.RESET, reason, capture_ms, frames, subject_id)

    def _append_pre_roll(self, frame: LandmarkFrame) -> None:
        self._pre_roll.append(frame)
        cutoff = frame.capture_ms - self.config.pre_roll_ms
        while self._pre_roll and self._pre_roll[0].capture_ms < cutoff:
            self._pre_roll.popleft()
        while len(self._pre_roll) > self.config.max_buffered_frames:
            self._pre_roll.popleft()

    def _finish(
        self,
        reason: SegmentReason,
        capture_ms: int,
        *,
        enforce_minimum: bool = True,
    ) -> SegmentEvent | None:
        frames = tuple(self._active_frames)
        trailing = tuple(self._possible_end)
        subject_id = self._subject_id
        if not frames:
            self._clear_detection(keep_temporal=True, trailing=trailing)
            return None
        semantic_start = self._candidate_start_ms or frames[0].capture_ms
        duration = frames[-1].capture_ms - semantic_start
        if enforce_minimum and duration < self.config.min_utterance_ms:
            event_type = SegmentEventType.DISCARDED
            event_reason = SegmentReason.TOO_SHORT
        else:
            event_type = SegmentEventType.COMMITTED
            event_reason = reason
        event = SegmentEvent(event_type, event_reason, capture_ms, frames, subject_id)
        self._clear_detection(keep_temporal=True, trailing=trailing)
        return event

    def _clear_detection(
        self,
        *,
        keep_temporal: bool,
        trailing: Sequence[LandmarkFrame] = (),
    ) -> None:
        self._pre_roll.clear()
        for frame in trailing:
            self._append_pre_roll(frame)
        self._active_frames.clear()
        self._possible_end.clear()
        self._state = SegmenterState.IDLE
        self._start_evidence = 0
        self._stop_evidence = 0
        self._candidate_start_ms = None
        self._last_motion_ms = None
        if not keep_temporal:
            self._pre_roll.clear()
            self._shoulder_widths.clear()
            self._last_hands_ms = None
            self._last_capture_ms = None
            self._previous_frame = None
