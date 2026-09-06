"""Temporal phrase segmentation for normalized sign-language landmark frames.

This module deliberately does not identify a sign or isolate a person. It
only finds likely phrase boundaries from hand presence, wrist velocity, rest
pauses, and hand drops. A trained segmenter can replace the thresholds later
without changing the output contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from statistics import median
from typing import Any, Iterable

from .processing_contracts import BoundaryEvent, LandmarkFrame


@dataclass(frozen=True)
class SegmenterConfig:
    """Stage-④ controls shared by both segmentation arms."""

    arm: str = "geometry_hysteresis"
    rest_velocity: float = 0.045
    pause_seconds: float = 0.42
    hand_drop_seconds: float = 0.32
    minimum_phrase_seconds: float = 0.12
    hysteresis_frames: int = 2
    wrist_height_threshold: float = 0.15
    wrist_height_seconds: float = 0.2
    stale_seconds: float = 2.0
    signing_space_margin: float = 0.35
    window_size: int = 16
    window_stride: int = 1
    beam_width: int = 10
    blank_class: str = "BLANK"


def _time_seconds(frame: dict[str, Any], index: int) -> float:
    value = frame.get("timestamp")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    milliseconds = frame.get("timestamp_ms")
    if isinstance(milliseconds, (int, float)):
        return float(milliseconds) / 1000.0
    return index / 30.0


def _point(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        return float(value.get("x", 0.0)), float(value.get("y", 0.0)), float(value.get("z", 0.0))
    except (TypeError, ValueError):
        return None


def hand_centers(frame: dict[str, Any]) -> list[tuple[float, float, float]]:
    """Return wrist centers in the normalized space when available."""
    normalized = frame.get("normalized_coordinates")
    if isinstance(normalized, list) and normalized:
        centers: list[tuple[float, float, float]] = []
        for hand in normalized:
            if not isinstance(hand, dict):
                continue
            landmarks = hand.get("landmarks", [])
            if not isinstance(landmarks, list) or not landmarks:
                continue
            wrist = _point(landmarks[0])
            if wrist is not None:
                centers.append(wrist)
        if centers:
            return centers
    return raw_hand_centers(frame)


def raw_hand_centers(frame: dict[str, Any]) -> list[tuple[float, float, float]]:
    """Return image-space wrist centers for the signing-space gate."""
    centers: list[tuple[float, float, float]] = []
    hands = frame.get("hands", [])
    if not isinstance(hands, list):
        return centers
    for hand in hands:
        if not isinstance(hand, dict):
            continue
        landmarks = hand.get("landmarks", [])
        if not isinstance(landmarks, list) or not landmarks:
            continue
        wrist = _point(landmarks[0])
        if wrist is not None:
            centers.append(wrist)
    return centers


def hand_present(frame: dict[str, Any]) -> bool:
    return bool(hand_centers(frame))


def _pose_point(frame: dict[str, Any], key: str) -> tuple[float, float, float] | None:
    return _point(frame.get(key))


def hands_in_signing_space(
    frame: dict[str, Any],
    margin: float = 0.35,
    wrist_height_threshold: float = 0.15,
    *,
    include_height: bool = True,
) -> bool:
    """Reject hands clearly outside the torso-relative signing region.

    When hips are unavailable, the body-normalized frontend has not supplied
    enough information for a height gate, so the function falls back to a
    conservative shoulder-width horizontal gate.
    """
    centers = raw_hand_centers(frame)
    if not centers:
        return False
    left_shoulder = _pose_point(frame, "left_shoulder")
    right_shoulder = _pose_point(frame, "right_shoulder")
    if not left_shoulder or not right_shoulder:
        return True
    shoulder_width = max(_distance(left_shoulder, right_shoulder), 0.1)
    midpoint_x = (left_shoulder[0] + right_shoulder[0]) / 2
    minimum_x = midpoint_x - shoulder_width * (1.0 + margin)
    maximum_x = midpoint_x + shoulder_width * (1.0 + margin)
    if any(point[0] < minimum_x or point[0] > maximum_x for point in centers):
        return False

    left_hip = _pose_point(frame, "left_hip")
    right_hip = _pose_point(frame, "right_hip")
    if not left_hip or not right_hip:
        return True
    hip_y = (left_hip[1] + right_hip[1]) / 2
    shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
    torso_height = max(abs(hip_y - shoulder_y), 0.1)
    # y increases downward in image coordinates; a wrist above the hip has a
    # positive torso-normalized height.
    if not include_height:
        return True
    return all(
        (hip_y - point[1]) / torso_height >= wrist_height_threshold
        for point in centers
    )


def _center(frame: dict[str, Any]) -> tuple[float, float, float] | None:
    values = hand_centers(frame)
    if not values:
        return None
    return tuple(sum(value[index] for value in values) / len(values) for index in range(3))


def _distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.sqrt(sum((first[index] - second[index]) ** 2 for index in range(3)))


def frame_velocity(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    previous_index: int,
    current_index: int,
) -> float:
    supplied_motion = current.get("hand_motion")
    if isinstance(supplied_motion, dict):
        value = supplied_motion.get("average_speed")
        if isinstance(value, (int, float)) and float(value) > 0:
            return float(value)
    if previous is None:
        return 0.0
    first = _center(previous)
    second = _center(current)
    if first is None or second is None:
        return 0.0
    elapsed = max(_time_seconds(current, current_index) - _time_seconds(previous, previous_index), 1 / 120)
    return _distance(first, second) / elapsed


@dataclass(frozen=True)
class PhraseSegment:
    phrase_id: str
    start_index: int
    end_index: int
    frames: list[dict[str, Any]]
    boundary_before: str | None
    boundary_after: str | None
    mean_velocity: float
    peak_velocity: float
    rest_baseline: dict[str, float] | None
    segmenter_arm: str = "geometry_hysteresis"
    boundary_events: list[BoundaryEvent] | None = None

    def to_dict(self, *, include_frames: bool = False) -> dict[str, Any]:
        start = self.frames[0] if self.frames else {}
        end = self.frames[-1] if self.frames else {}
        value: dict[str, Any] = {
            "phrase_id": self.phrase_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "start_timestamp": start.get("timestamp"),
            "end_timestamp": end.get("timestamp"),
            "boundary_before": self.boundary_before,
            "boundary_after": self.boundary_after,
            "mean_velocity": round(self.mean_velocity, 6),
            "peak_velocity": round(self.peak_velocity, 6),
            "rest_baseline": self.rest_baseline,
            "segmenter_arm": self.segmenter_arm,
            "boundary_events": [
                event.to_dict() for event in (self.boundary_events or [])
            ],
        }
        if include_frames:
            value["frames"] = self.frames
        return value


class PhraseSegmenter:
    """Threshold-based segmenter with explicit, inspectable boundaries."""

    def __init__(
        self,
        *,
        config: SegmenterConfig | None = None,
        arm: str = "geometry_hysteresis",
        rest_velocity: float = 0.045,
        pause_seconds: float = 0.42,
        hand_drop_seconds: float = 0.32,
        minimum_phrase_seconds: float = 0.12,
        hysteresis_frames: int = 2,
        wrist_height_threshold: float = 0.15,
        wrist_height_seconds: float = 0.2,
        stale_seconds: float = 2.0,
        signing_space_margin: float = 0.35,
    ) -> None:
        if arm != "geometry_hysteresis":
            raise ValueError("PhraseSegmenter only implements geometry_hysteresis")
        if config is not None and config.arm != "geometry_hysteresis":
            raise ValueError("PhraseSegmenter requires a geometry_hysteresis config")
        self.config = config or SegmenterConfig(
            arm=arm,
            rest_velocity=rest_velocity,
            pause_seconds=pause_seconds,
            hand_drop_seconds=hand_drop_seconds,
            minimum_phrase_seconds=minimum_phrase_seconds,
            hysteresis_frames=hysteresis_frames,
            wrist_height_threshold=wrist_height_threshold,
            wrist_height_seconds=wrist_height_seconds,
            stale_seconds=stale_seconds,
            signing_space_margin=signing_space_margin,
        )
        self.arm = self.config.arm
        self.rest_velocity = self.config.rest_velocity
        self.pause_seconds = self.config.pause_seconds
        self.hand_drop_seconds = self.config.hand_drop_seconds
        self.minimum_phrase_seconds = self.config.minimum_phrase_seconds
        self.hysteresis_frames = max(1, self.config.hysteresis_frames)
        self.stale_seconds = self.config.stale_seconds
        self.signing_space_margin = self.config.signing_space_margin
        self.last_events: list[BoundaryEvent] = []

    def segment(
        self,
        frames: Iterable[dict[str, Any] | LandmarkFrame],
    ) -> list[PhraseSegment]:
        landmark_frames = self.landmark_frames(frames)
        values = [frame.to_dict() for frame in landmark_frames]
        if not values:
            self.last_events = []
            return []

        segments: list[PhraseSegment] = []
        active_start: int | None = None
        last_active: int | None = None
        pause_start: int | None = None
        drop_start: int | None = None
        buffered_start: int | None = None
        active_evidence = 0
        rest_evidence = 0
        absence_start: int | None = None
        stale_emitted = False
        height_gate_start: int | None = None
        boundary_before: str | None = None
        velocities: list[float] = []
        rest_positions: list[tuple[float, float, float]] = []
        event_log: list[BoundaryEvent] = []

        def close(end_index: int, boundary_after: str) -> None:
            nonlocal active_start, last_active, pause_start, drop_start, buffered_start
            nonlocal boundary_before, velocities, rest_positions
            nonlocal active_evidence, rest_evidence
            if active_start is None or last_active is None or end_index < active_start:
                return
            actual_end = min(end_index, last_active)
            segment_frames = values[active_start : actual_end + 1]
            if not segment_frames:
                return
            baseline = None
            if rest_positions:
                baseline = {
                    "x": round(median(value[0] for value in rest_positions), 6),
                    "y": round(median(value[1] for value in rest_positions), 6),
                    "z": round(median(value[2] for value in rest_positions), 6),
                }
            phrase_index = len(segments) + 1
            segment_events = [
                BoundaryEvent(
                    event_type="sign_start",
                    frame_index=active_start,
                    reason=boundary_before or "stream_start",
                    confidence=0.85,
                ),
                BoundaryEvent(
                    event_type="sign_end",
                    frame_index=actual_end,
                    reason=boundary_after,
                    confidence=0.85,
                ),
                BoundaryEvent(
                    event_type="utterance_boundary",
                    frame_index=actual_end,
                    reason=boundary_after,
                    confidence=0.8 if boundary_after != "end_of_stream" else 0.7,
                ),
            ]
            event_log.extend(segment_events)
            segments.append(
                PhraseSegment(
                    phrase_id=f"phrase_{phrase_index:03d}",
                    start_index=active_start,
                    end_index=actual_end,
                    frames=segment_frames,
                    boundary_before=boundary_before,
                    boundary_after=boundary_after,
                    mean_velocity=sum(velocities) / len(velocities) if velocities else 0.0,
                    peak_velocity=max(velocities, default=0.0),
                    rest_baseline=baseline,
                    segmenter_arm=self.arm,
                    boundary_events=segment_events,
                )
            )
            active_start = None
            last_active = None
            pause_start = None
            drop_start = None
            buffered_start = None
            active_evidence = 0
            rest_evidence = 0
            boundary_before = boundary_after
            velocities = []
            rest_positions = []

        for index, frame in enumerate(values):
            previous = values[index - 1] if index else None
            velocity = frame_velocity(previous, frame, index - 1, index) if previous else 0.0
            now = _time_seconds(frame, index)
            horizontal_space = hand_present(frame) and hands_in_signing_space(
                frame,
                self.signing_space_margin,
                self.config.wrist_height_threshold,
                include_height=False,
            )
            height_space = horizontal_space and hands_in_signing_space(
                frame,
                self.signing_space_margin,
                self.config.wrist_height_threshold,
            )
            if horizontal_space and not height_space:
                if height_gate_start is None:
                    height_gate_start = index
                height_grace = now - _time_seconds(values[height_gate_start], height_gate_start)
                height_space = height_grace < self.config.wrist_height_seconds
            else:
                height_gate_start = None
            present = horizontal_space and height_space
            if present:
                absence_start = None
                stale_emitted = False
                if velocity > self.rest_velocity:
                    active_evidence += 1
                    rest_evidence = 0
                else:
                    rest_evidence += 1
                    active_evidence = 0
                if active_start is None:
                    if buffered_start is None:
                        buffered_start = index
                    # Stationary frames before the first movement establish
                    # a replay buffer. Once movement commits the state, the
                    # buffered run-up is included instead of discarded.
                    buffered_duration = now - _time_seconds(values[buffered_start], buffered_start)
                    movement_committed = active_evidence >= self.hysteresis_frames
                    if index == 0 or movement_committed:
                        active_start = buffered_start
                        last_active = index
                        velocities = [velocity]
                    elif buffered_duration >= self.pause_seconds:
                        buffered_start = index
                    else:
                        continue
                elif velocity <= self.rest_velocity:
                    if pause_start is None:
                        pause_start = index
                    position = _center(frame)
                    if position is not None:
                        rest_positions.append(position)
                    pause_duration = now - _time_seconds(values[pause_start], pause_start)
                    if pause_duration >= self.pause_seconds and pause_start > active_start:
                        close(pause_start - 1, "rest_pause")
                    continue
                else:
                    pause_start = None
                    rest_positions = []
                last_active = index
                velocities.append(velocity)
                drop_start = None
            else:
                if absence_start is None:
                    absence_start = index
                absence_duration = now - _time_seconds(values[absence_start], absence_start)
                if absence_duration >= self.stale_seconds and not stale_emitted:
                    stale_event = BoundaryEvent(
                        event_type="stale_state",
                        frame_index=index,
                        reason="no_hands_for_stale_interval",
                        confidence=0.9,
                    )
                    event_log.append(stale_event)
                    stale_emitted = True
                if active_start is not None:
                    if drop_start is None:
                        drop_start = index
                    drop_duration = now - _time_seconds(values[drop_start], drop_start)
                    if drop_duration >= self.hand_drop_seconds:
                        close(drop_start - 1, "hand_drop")

        if active_start is not None and last_active is not None:
            close(last_active, "end_of_stream")
        self.last_events = event_log
        return segments

    @staticmethod
    def landmark_frames(
        frames: Iterable[dict[str, Any] | LandmarkFrame],
    ) -> list[LandmarkFrame]:
        """Normalize either API dictionaries or typed LandmarkFrame values."""
        return LandmarkFrame.from_sequence(frames)

    def thresholds(self) -> dict[str, float]:
        return {
            "rest_velocity": self.rest_velocity,
            "pause_seconds": self.pause_seconds,
            "hand_drop_seconds": self.hand_drop_seconds,
            "minimum_phrase_seconds": self.minimum_phrase_seconds,
            "hysteresis_frames": float(self.hysteresis_frames),
            "wrist_height_threshold": self.config.wrist_height_threshold,
            "wrist_height_seconds": self.config.wrist_height_seconds,
            "stale_seconds": self.stale_seconds,
            "signing_space_margin": self.signing_space_margin,
        }


class SlidingWindowSegmenter:
    """Arm B: fixed sliding windows with an explicit blank-class contract."""

    def __init__(
        self,
        *,
        window_size: int = 16,
        stride: int = 1,
        beam_width: int = 10,
        blank_class: str = "BLANK",
    ) -> None:
        self.window_size = max(1, window_size)
        self.stride = max(1, stride)
        self.beam_width = max(1, beam_width)
        self.blank_class = blank_class
        self.arm = "sliding_window_blank"
        self.last_events: list[BoundaryEvent] = []

    def segment(
        self,
        frames: Iterable[dict[str, Any] | LandmarkFrame],
    ) -> list[PhraseSegment]:
        typed = PhraseSegmenter.landmark_frames(frames)
        values = [frame.to_dict() for frame in typed]
        if not values:
            self.last_events = []
            return []
        segments: list[PhraseSegment] = []
        events: list[BoundaryEvent] = []
        starts = range(0, len(values), self.stride)
        for phrase_index, start in enumerate(starts, start=1):
            end = min(start + self.window_size, len(values))
            window = values[start:end]
            if not window:
                continue
            speeds = [
                frame_velocity(values[index - 1], values[index], index - 1, index)
                for index in range(start + 1, end)
            ]
            window_events = [
                BoundaryEvent("window_start", start, "sliding_window", self.arm, 0.7),
                BoundaryEvent("window_end", end - 1, "sliding_window", self.arm, 0.7),
            ]
            if end == len(values):
                window_events.append(
                    BoundaryEvent("utterance_boundary", end - 1, "end_of_stream", self.arm, 0.7)
                )
            events.extend(window_events)
            segments.append(
                PhraseSegment(
                    phrase_id=f"window_{phrase_index:04d}",
                    start_index=start,
                    end_index=end - 1,
                    frames=window,
                    boundary_before="sliding_window",
                    boundary_after="end_of_stream" if end == len(values) else "sliding_window",
                    mean_velocity=sum(speeds) / len(speeds) if speeds else 0.0,
                    peak_velocity=max(speeds, default=0.0),
                    rest_baseline=None,
                    segmenter_arm=self.arm,
                    boundary_events=window_events,
                )
            )
            if end == len(values):
                break
        self.last_events = events
        return segments

    def thresholds(self) -> dict[str, float]:
        return {
            "window_size": float(self.window_size),
            "stride": float(self.stride),
            "beam_width": float(self.beam_width),
        }


def create_segmenter(
    arm: str = "geometry_hysteresis",
    **kwargs: Any,
) -> PhraseSegmenter | SlidingWindowSegmenter:
    """Select either stage-④ arm without changing downstream consumers."""
    if arm == "geometry_hysteresis":
        return PhraseSegmenter(arm=arm, **kwargs)
    if arm == "sliding_window_blank":
        return SlidingWindowSegmenter(**kwargs)
    raise ValueError(f"unsupported segmenter arm: {arm}")
