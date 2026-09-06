"""RTMLib Wholebody adapter for live browser frames.

RTMLib combines a person detector with RTMPose/RTMW. The model returns one
whole-body result containing body joints, 68 face points, and 21 points for
each hand. This keeps the browser free of MediaPipe and gives the Flutter
layer the same normalized hand contract it already understands.
"""

from __future__ import annotations

import importlib
from typing import Any


class WholebodyRuntimeUnavailable(RuntimeError):
    """Raised when RTMLib or its ONNX runtime is not installed."""


class WholebodyRtmlibAdapter:
    def __init__(self) -> None:
        try:
            self._cv2 = importlib.import_module("cv2")
            self._numpy = importlib.import_module("numpy")
            self._configure_download_certificates()
            rtmlib = importlib.import_module("rtmlib")
            self._model = rtmlib.Wholebody(
                mode="lightweight",
                to_openpose=True,
                backend="onnxruntime",
                device="cpu",
            )
        except ImportError as error:
            raise WholebodyRuntimeUnavailable(
                "Install backend/requirements-rtmlib.txt to enable RTMPose whole-body tracking."
            ) from error
        except Exception as error:
            raise WholebodyRuntimeUnavailable(
                f"RTMPose whole-body model could not start: {error}"
            ) from error

    @staticmethod
    def _configure_download_certificates() -> None:
        """Give RTMLib's urllib downloader a CA bundle on macOS/Python."""
        try:
            import certifi
            import ssl
        except ImportError:
            return
        ssl._create_default_https_context = lambda: ssl.create_default_context(
            cafile=certifi.where()
        )

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        image = self._cv2.imdecode(
            self._numpy.frombuffer(image_bytes, dtype=self._numpy.uint8),
            self._cv2.IMREAD_COLOR,
        )
        if image is None:
            raise ValueError("The tracking frame is not a valid JPEG or PNG.")
        height, width = image.shape[:2]
        keypoints, scores = self._model(image)
        if len(keypoints) == 0:
            return self._empty_result()

        # The lightweight whole-body model returns OpenPose-style 134 points:
        # body 0..17, face 24..91, left hand 92..112, right hand 113..133.
        instance_index = self._best_instance(scores)
        points = keypoints[instance_index]
        point_scores = scores[instance_index]
        left_hand = self._hand(points, point_scores, 92, width, height)
        right_hand = self._hand(points, point_scores, 113, width, height)
        hands = [hand for hand in (left_hand, right_hand) if hand is not None]
        face = self._face(points, point_scores, width, height)
        left_shoulder = self._point(points[5], point_scores[5], width, height)
        right_shoulder = self._point(points[2], point_scores[2], width, height)
        person_bounding_box = self._person_bounding_box(
            points,
            point_scores,
            width,
            height,
            hands,
        )
        confidence = max(
            [hand["confidence"] for hand in hands]
            + [left_shoulder["visibility"], right_shoulder["visibility"]]
            + ([face["confidence"]] if face else [])
            + [0.0]
        )
        return {
            "provider": "rtmlib_rtmpose_wholebody",
            "processing_confidence": round(confidence, 6),
            "hands": hands,
            "face": face,
            "left_shoulder": left_shoulder,
            "right_shoulder": right_shoulder,
            "person_bounding_box": person_bounding_box,
        }

    def _hand(
        self,
        points: Any,
        scores: Any,
        start: int,
        width: int,
        height: int,
    ) -> dict[str, Any] | None:
        hand_scores = [float(value) for value in scores[start : start + 21]]
        if not hand_scores or max(hand_scores) < 0.2:
            return None
        landmarks = [
            self._point(points[start + index], hand_scores[index], width, height)
            for index in range(21)
        ]
        xs = [point["x"] for point in landmarks]
        ys = [point["y"] for point in landmarks]
        return {
            # OpenPose ordering in RTMW is left hand first, right hand second.
            "handedness": "left" if start == 92 else "right",
            "confidence": round(sum(hand_scores) / len(hand_scores), 6),
            "bounding_box": [min(xs), min(ys), max(xs), max(ys)],
            "landmarks": [
                {key: value for key, value in point.items() if key != "visibility"}
                for point in landmarks
            ],
        }

    def _face(
        self,
        points: Any,
        scores: Any,
        width: int,
        height: int,
    ) -> dict[str, Any] | None:
        face_scores = [float(value) for value in scores[24:92]]
        if not face_scores or max(face_scores) < 0.2:
            return None
        face_points = [
            self._point(points[24 + index], face_scores[index], width, height)
            for index in range(68)
        ]
        visible = [point for point, score in zip(face_points, face_scores) if score >= 0.2]
        if not visible:
            return None
        left_eye = face_points[36] if len(face_points) > 45 else visible[0]
        right_eye = face_points[45] if len(face_points) > 45 else visible[-1]
        import math

        roll = math.atan2(right_eye["y"] - left_eye["y"], right_eye["x"] - left_eye["x"])
        return {
            "confidence": round(sum(face_scores) / len(face_scores), 6),
            "label": "face_landmarks_only",
            "head_tilt": roll,
            "head_roll": roll,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_pose_source": "rtmpose_face_eye_line",
            "landmarks": [
                {
                    "index": index,
                    **point,
                }
                for index, point in enumerate(face_points)
                if face_scores[index] >= 0.2
            ],
            "blendshapes": {},
        }

    @staticmethod
    def _point(point: Any, score: float, width: int, height: int) -> dict[str, float]:
        return {
            "x": max(0.0, min(1.0, float(point[0]) / width)),
            "y": max(0.0, min(1.0, float(point[1]) / height)),
            "z": 0.0,
            "visibility": max(0.0, min(1.0, float(score))),
        }

    @staticmethod
    def _best_instance(scores: Any) -> int:
        if len(scores) == 1:
            return 0
        totals = scores[:, :18].mean(axis=1)
        return int(totals.argmax())

    def _person_bounding_box(
        self,
        points: Any,
        scores: Any,
        width: int,
        height: int,
        hands: list[dict[str, Any]],
    ) -> list[float] | None:
        visible = [
            self._point(points[index], scores[index], width, height)
            for index in range(min(18, len(points)))
            if float(scores[index]) >= 0.2
        ]
        for hand in hands:
            visible.extend(
                {"x": landmark["x"], "y": landmark["y"]}
                for landmark in hand["landmarks"]
            )
        if len(visible) < 2:
            return None
        return [
            max(0.0, min(1.0, min(point["x"] for point in visible))),
            max(0.0, min(1.0, min(point["y"] for point in visible))),
            max(0.0, min(1.0, max(point["x"] for point in visible))),
            max(0.0, min(1.0, max(point["y"] for point in visible))),
        ]

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        return {
            "provider": "rtmlib_rtmpose_wholebody",
            "processing_confidence": 0.0,
            "hands": [],
            "face": None,
            "left_shoulder": None,
            "right_shoulder": None,
            "person_bounding_box": None,
        }
