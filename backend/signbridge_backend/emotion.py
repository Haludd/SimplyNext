"""DeepFace emotion adapter based on the referenced OpenCV example.

The original example owns the webcam and draws the result in an OpenCV window.
SignBridge already owns the browser camera, so this module accepts one encoded
image at a time and returns JSON instead.
"""

from __future__ import annotations

from threading import Lock
from typing import Any


class EmotionAnalysisError(ValueError):
    """Raised when an image cannot be decoded or analysed."""


class EmotionDependenciesMissing(RuntimeError):
    """Raised when the optional DeepFace dependencies are not installed."""


class DeepFaceEmotionAnalyzer:
    """Run the linked repository's OpenCV + DeepFace emotion pipeline."""

    model_name = "DeepFace"

    def __init__(self) -> None:
        self._runtime_lock = Lock()
        self._cv2: Any | None = None
        self._numpy: Any | None = None
        self._deepface: Any | None = None
        self._face_cascade: Any | None = None

    def _load_runtime(self) -> tuple[Any, Any, Any, Any]:
        """Load the image stack and emotion model once per backend process."""
        if (
            self._cv2 is not None
            and self._numpy is not None
            and self._deepface is not None
            and self._face_cascade is not None
        ):
            return self._cv2, self._numpy, self._deepface, self._face_cascade

        with self._runtime_lock:
            if (
                self._cv2 is not None
                and self._numpy is not None
                and self._deepface is not None
                and self._face_cascade is not None
            ):
                return self._cv2, self._numpy, self._deepface, self._face_cascade

            try:
                import cv2
                import numpy as np
            except ImportError as error:  # keep the normal backend stdlib-only
                raise EmotionDependenciesMissing(
                    "Install backend/requirements.txt to enable DeepFace emotion analysis."
                ) from error

            try:
                from deepface import DeepFace
            except ImportError as error:
                raise EmotionDependenciesMissing(
                    "Install backend/requirements.txt to enable DeepFace emotion analysis."
                ) from error

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            if face_cascade.empty():
                raise EmotionAnalysisError("OpenCV face detector could not be loaded")

            # Loading the model here turns the first camera request into a
            # normal request instead of making it pay the model-startup cost.
            DeepFace.build_model("Emotion", task="facial_attribute")
            self._cv2 = cv2
            self._numpy = np
            self._deepface = DeepFace
            self._face_cascade = face_cascade
            return cv2, np, DeepFace, face_cascade

    def warm_up(self) -> None:
        """Load dependencies and model weights before serving camera requests."""
        self._load_runtime()

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        if not image_bytes:
            raise EmotionAnalysisError("image body is empty")

        cv2, np, DeepFace, face_cascade = self._load_runtime()

        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            raise EmotionAnalysisError("image is not a valid JPEG or PNG")

        # This follows the referenced repository: Haar-cascade face detection,
        # RGB face crop, then DeepFace emotion analysis.
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        if len(faces) == 0:
            return {
                "status": "no_face",
                "dominant_emotion": "not detected",
                "confidence": 0.0,
                "emotions": {},
                "model": self.model_name,
                "source": "deepface",
            }

        # The original example analyses every face. The frontend displays one
        # emotion signal, so use the largest detected face (usually the person
        # closest to the camera).
        x, y, width, height = max(faces, key=lambda face: int(face[2]) * int(face[3]))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_roi = rgb_frame[y : y + height, x : x + width]
        result = DeepFace.analyze(
            face_roi,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="skip",
            align=False,
            silent=True,
        )
        if isinstance(result, list):
            result = result[0] if result else {}
        if not isinstance(result, dict):
            raise EmotionAnalysisError("DeepFace returned an unexpected result")

        raw_emotions = result.get("emotion") or {}
        emotions = {
            str(label).lower(): round(float(score) / 100.0, 6)
            for label, score in raw_emotions.items()
        }
        dominant = str(result.get("dominant_emotion") or "not detected").lower()
        confidence = max(emotions.values(), default=0.0)
        return {
            "status": "ok",
            "dominant_emotion": dominant,
            "confidence": round(confidence, 6),
            "emotions": emotions,
            "model": self.model_name,
            "source": "deepface",
            "face_box": {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            },
        }
