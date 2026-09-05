"""Fast HSEmotion/EmotiEffLib facial-expression adapter."""

from __future__ import annotations

from threading import Lock
from typing import Any


class HSEmotionAnalysisError(ValueError):
    """Raised when HSEmotion cannot analyse an image."""


class HSEmotionDependenciesMissing(RuntimeError):
    """Raised when the HSEmotion package is not installed."""


class HSEmotionModelUnavailable(RuntimeError):
    """Raised when HSEmotion cannot load or download its checkpoint."""


class HSEmotionEmotionAnalyzer:
    """Run HSEmotion's seven-expression EfficientNet ONNX model."""

    labels = (
        "angry",
        "disgust",
        "fear",
        "happy",
        "neutral",
        "sad",
        "surprise",
    )
    model_name = "HSEmotion EfficientNet-B2"

    def __init__(self, model_name: str = "enet_b2_7") -> None:
        self.checkpoint_name = model_name
        self._runtime_lock = Lock()
        self._cv2: Any | None = None
        self._numpy: Any | None = None
        self._recognizer: Any | None = None
        self._face_cascade: Any | None = None

    def _load_runtime(self) -> tuple[Any, Any, Any, Any]:
        if (
            self._cv2 is not None
            and self._numpy is not None
            and self._recognizer is not None
            and self._face_cascade is not None
        ):
            return self._cv2, self._numpy, self._recognizer, self._face_cascade

        with self._runtime_lock:
            if (
                self._cv2 is not None
                and self._numpy is not None
                and self._recognizer is not None
                and self._face_cascade is not None
            ):
                return self._cv2, self._numpy, self._recognizer, self._face_cascade

            try:
                import cv2
                import numpy as np
            except ImportError as error:
                raise HSEmotionDependenciesMissing(
                    "Install backend/requirements.txt to enable HSEmotion."
                ) from error

            try:
                # hsemotion-onnx imports urllib.request but accesses it as an
                # attribute. Importing it first keeps that package compatible
                # with this Python runtime.
                import urllib.request  # noqa: F401
                from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
            except ImportError as error:
                raise HSEmotionDependenciesMissing(
                    "Install backend/requirements.txt to enable HSEmotion."
                ) from error

            try:
                recognizer = HSEmotionRecognizer(model_name=self.checkpoint_name)
            except Exception as error:
                raise HSEmotionModelUnavailable(
                    f"HSEmotion model {self.checkpoint_name!r} could not be loaded."
                ) from error

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            if face_cascade.empty():
                raise HSEmotionAnalysisError("OpenCV face detector could not be loaded")

            self._cv2 = cv2
            self._numpy = np
            self._recognizer = recognizer
            self._face_cascade = face_cascade
            return cv2, np, recognizer, face_cascade

    def warm_up(self) -> None:
        """Load the checkpoint before the first browser request."""
        self._load_runtime()

    @staticmethod
    def _normalise_label(label: str) -> str:
        return {
            "anger": "angry",
            "happiness": "happy",
            "sadness": "sad",
        }.get(label.lower(), label.lower())

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        if not image_bytes:
            raise HSEmotionAnalysisError("image body is empty")

        cv2, np, recognizer, face_cascade = self._load_runtime()
        frame = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise HSEmotionAnalysisError("image is not a valid JPEG or PNG")

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
                "source": "hsemotion",
            }

        x, y, width, height = max(faces, key=lambda face: int(face[2]) * int(face[3]))
        face_roi = frame[y : y + height, x : x + width]
        try:
            dominant, raw_scores = recognizer.predict_emotions(
                face_roi,
                logits=False,
            )
        except Exception as error:
            raise HSEmotionAnalysisError("HSEmotion could not analyse the face") from error

        class_names = getattr(recognizer, "idx_to_class", {})
        emotions = {
            self._normalise_label(str(class_names.get(index, self.labels[index]))): round(
                float(score), 6
            )
            for index, score in enumerate(raw_scores)
            if index < len(self.labels)
        }
        dominant_emotion = self._normalise_label(str(dominant))
        return {
            "status": "ok",
            "dominant_emotion": dominant_emotion,
            "confidence": round(max(emotions.values(), default=0.0), 6),
            "emotions": emotions,
            "model": self.model_name,
            "source": "hsemotion",
            "face_box": {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            },
        }
