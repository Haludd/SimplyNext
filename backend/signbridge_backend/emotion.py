"""DeepFace emotion adapter based on the referenced OpenCV example.

The original example owns the webcam and draws the result in an OpenCV window.
SignBridge already owns the browser camera, so this module accepts one encoded
image at a time and returns JSON instead.
"""

from __future__ import annotations

from typing import Any


class EmotionAnalysisError(ValueError):
    """Raised when an image cannot be decoded or analysed."""


class EmotionDependenciesMissing(RuntimeError):
    """Raised when the optional DeepFace dependencies are not installed."""


class DeepFaceEmotionAnalyzer:
    """Run the linked repository's OpenCV + DeepFace emotion pipeline."""

    model_name = "DeepFace"

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        if not image_bytes:
            raise EmotionAnalysisError("image body is empty")

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

        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            raise EmotionAnalysisError("image is not a valid JPEG or PNG")

        # This follows the referenced repository: Haar-cascade face detection,
        # RGB face crop, then DeepFace emotion analysis.
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
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
            }

        # The original example analyses every face. The frontend displays one
        # emotion signal, so use the largest detected face (usually the person
        # closest to the camera).
        x, y, width, height = max(faces, key=lambda face: int(face[2]) * int(face[3]))
        face_roi = rgb_frame[y : y + height, x : x + width]
        result = DeepFace.analyze(
            face_roi,
            actions=["emotion"],
            enforce_detection=False,
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
            "face_box": {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            },
        }
