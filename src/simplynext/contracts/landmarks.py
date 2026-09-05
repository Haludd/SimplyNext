"""Compact, fixed-layout landmark stream contracts."""

from __future__ import annotations

from types import MappingProxyType
from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .common import Confidence, ContractModel, Identifier

LANDMARK_SCHEMA_VERSION: Literal["1.0"] = "1.0"
MAX_CONTRACT_BATCH_FRAMES = 32

# MediaPipe Hand Landmarker order. Both hands use this same anatomical order.
HAND_LANDMARK_NAMES = (
    "wrist",
    "thumb_cmc",
    "thumb_mcp",
    "thumb_ip",
    "thumb_tip",
    "index_mcp",
    "index_pip",
    "index_dip",
    "index_tip",
    "middle_mcp",
    "middle_pip",
    "middle_dip",
    "middle_tip",
    "ring_mcp",
    "ring_pip",
    "ring_dip",
    "ring_tip",
    "pinky_mcp",
    "pinky_pip",
    "pinky_dip",
    "pinky_tip",
)

# A small upper-body layout used for body-relative normalization and motion.
POSE_LANDMARK_NAMES = (
    "nose",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
)
POSE_LANDMARK_INDICES = MappingProxyType(
    {
        "nose": 0,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
    }
)

# Face Mesh indices selected for brow, eye, mouth, head, and chin signals.
FACE_LANDMARK_NAMES = (
    "nose_tip",
    "chin",
    "left_brow_outer",
    "left_brow_mid",
    "left_brow_inner",
    "right_brow_inner",
    "right_brow_mid",
    "right_brow_outer",
    "left_eye_upper",
    "left_eye_lower",
    "right_eye_upper",
    "right_eye_lower",
    "mouth_left",
    "upper_lip",
    "lower_lip",
    "mouth_right",
)
FACE_LANDMARK_INDICES = MappingProxyType(
    {
        "nose_tip": 1,
        "chin": 152,
        "left_brow_outer": 70,
        "left_brow_mid": 105,
        "left_brow_inner": 107,
        "right_brow_inner": 336,
        "right_brow_mid": 334,
        "right_brow_outer": 300,
        "left_eye_upper": 159,
        "left_eye_lower": 145,
        "right_eye_upper": 386,
        "right_eye_lower": 374,
        "mouth_left": 61,
        "upper_lip": 13,
        "lower_lip": 14,
        "mouth_right": 291,
    }
)

# x, y, and z are MediaPipe-normalized camera coordinates. The fourth value is
# a unified confidence/visibility score. A zero confidence marks a missing point.
ImageCoordinate = Annotated[float, Field(ge=-4.0, le=4.0, allow_inf_nan=False)]
RelativeDepth = Annotated[float, Field(ge=-10.0, le=10.0, allow_inf_nan=False)]
ImageDimension = Annotated[int, Field(ge=1, le=100_000)]
LandmarkPoint: TypeAlias = tuple[
    ImageCoordinate,
    ImageCoordinate,
    RelativeDepth,
    Confidence,
]
HandLandmarks: TypeAlias = Annotated[
    tuple[LandmarkPoint, ...],
    Field(min_length=len(HAND_LANDMARK_NAMES), max_length=len(HAND_LANDMARK_NAMES)),
]
PoseLandmarks: TypeAlias = Annotated[
    tuple[LandmarkPoint, ...],
    Field(min_length=len(POSE_LANDMARK_NAMES), max_length=len(POSE_LANDMARK_NAMES)),
]
FaceLandmarks: TypeAlias = Annotated[
    tuple[LandmarkPoint, ...],
    Field(min_length=len(FACE_LANDMARK_NAMES), max_length=len(FACE_LANDMARK_NAMES)),
]


class LandmarkLayout(ContractModel):
    """Self-describing layout sent once during session negotiation."""

    version: Literal["1.0"] = LANDMARK_SCHEMA_VERSION
    point_format: Literal["x,y,z,confidence"] = "x,y,z,confidence"
    hand: tuple[str, ...] = HAND_LANDMARK_NAMES
    pose: tuple[str, ...] = POSE_LANDMARK_NAMES
    face: tuple[str, ...] = FACE_LANDMARK_NAMES


class CameraGeometry(ContractModel):
    """Camera transform metadata retained for validation and replay."""

    source_width: ImageDimension
    source_height: ImageDimension
    rotation_degrees: Literal[0, 90, 180, 270]
    mirrored_input: bool
    coordinates_canonical: Literal[True] = True


class LandmarkFrame(ContractModel):
    """One timestamped frame in the negotiated fixed layout."""

    seq: int = Field(ge=0)
    capture_ms: int = Field(ge=0)
    subject_id: Identifier | None = None
    pose: PoseLandmarks | None = None
    left_hand: HandLandmarks | None = None
    right_hand: HandLandmarks | None = None
    face: FaceLandmarks | None = None
    left_hand_score: Confidence | None = None
    right_hand_score: Confidence | None = None
    tracking_confidence: Confidence | None = None

    @model_validator(mode="after")
    def scores_require_corresponding_hands(self) -> LandmarkFrame:
        if self.left_hand_score is not None and self.left_hand is None:
            raise ValueError("left_hand_score requires left_hand landmarks")
        if self.right_hand_score is not None and self.right_hand is None:
            raise ValueError("right_hand_score requires right_hand landmarks")
        return self


class LandmarkBatch(ContractModel):
    """A small ordered micro-batch sent over the session WebSocket."""

    type: Literal["landmark_batch"] = "landmark_batch"
    schema_version: Literal["1.0"] = LANDMARK_SCHEMA_VERSION
    session_id: UUID
    batch_seq: int = Field(ge=0)
    camera: CameraGeometry
    frames: Annotated[
        tuple[LandmarkFrame, ...],
        Field(min_length=1, max_length=MAX_CONTRACT_BATCH_FRAMES),
    ]
    dropped_before: int = Field(default=0, ge=0, le=1_000_000)

    @field_validator("frames")
    @classmethod
    def frames_are_strictly_ordered(
        cls,
        frames: tuple[LandmarkFrame, ...],
    ) -> tuple[LandmarkFrame, ...]:
        for previous, current in zip(frames, frames[1:], strict=False):
            if current.seq <= previous.seq:
                raise ValueError("frame seq values must be strictly increasing")
            if current.capture_ms <= previous.capture_ms:
                raise ValueError("frame capture_ms values must be strictly increasing")
        return frames

    @model_validator(mode="after")
    def contains_canonical_coordinates(self) -> LandmarkBatch:
        # The Literal field already rejects false. Keeping the invariant explicit
        # makes it visible to generated JSON Schema and code readers.
        if not self.camera.coordinates_canonical:
            raise ValueError("landmarks must be canonicalized on the client")
        return self
