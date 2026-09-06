"""Optional CV4ED affect adapter.

This follows the linked project's ``src/inference/run_hsemotion.py`` contract:
the input is a cropped BGR face, the ONNX model returns emotion logits plus
valence and arousal outputs, and the frame-level results are aggregated by the
caller. The browser supplies the face crop so the backend does not need a
second face detector or to persist camera frames.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any


class Cv4edAffectUnavailable(RuntimeError):
    """Raised when the CV4ED ONNX model or its runtime is unavailable."""


class Cv4edAffectAdapter:
    """Run the CV4ED/HSEmotion ONNX model on one face crop."""

    _INDEX_TO_CLASS = (
        "Anger",
        "Contempt",
        "Disgust",
        "Fear",
        "Happiness",
        "Neutral",
        "Sadness",
        "Surprise",
    )

    def __init__(self, model_path: str | Path | None = None) -> None:
        try:
            self._cv2 = importlib.import_module("cv2")
            self._numpy = importlib.import_module("numpy")
            onnxruntime = importlib.import_module("onnxruntime")
        except ImportError as error:
            raise Cv4edAffectUnavailable(
                "Install backend/requirements-cv4ed-affect.txt to enable the CV4ED affect model."
            ) from error

        configured_path = model_path or os.environ.get("SIGNBRIDGE_CV4ED_ONNX_PATH")
        if configured_path:
            path = Path(configured_path)
        else:
            path = Path(__file__).parents[1] / "models" / "hsemotion-onnx" / "hsemotion_1280.onnx"
        if not path.is_file():
            raise Cv4edAffectUnavailable(
                "CV4ED model weights are missing. Set SIGNBRIDGE_CV4ED_ONNX_PATH "
                f"to the hsemotion ONNX file (looked at {path})."
            )

        self.model_path = path
        self._session = onnxruntime.InferenceSession(
            str(path),
            providers=["CPUExecutionProvider"],
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_names = [output.name for output in self._session.get_outputs()]
        if len(self._output_names) < 4:
            raise Cv4edAffectUnavailable(
                "The CV4ED ONNX model must expose emotion, valence, and arousal outputs."
            )

    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        image = self._cv2.imdecode(
            self._numpy.frombuffer(image_bytes, dtype=self._numpy.uint8),
            self._cv2.IMREAD_COLOR,
        )
        if image is None:
            raise ValueError("The face crop is not a valid JPEG or PNG.")

        outputs = self._session.run(
            self._output_names,
            {self._input_name: self._preprocess(image)},
        )
        emotion_logits = self._numpy.asarray(outputs[1]).reshape(-1)
        emotion_probabilities = self._softmax(emotion_logits[:8])
        if not emotion_probabilities:
            raise ValueError("The CV4ED model returned no emotion scores.")
        label_index = max(
            range(len(emotion_probabilities)),
            key=emotion_probabilities.__getitem__,
        )
        scores = {
            self._INDEX_TO_CLASS[index].lower(): round(float(score), 6)
            for index, score in enumerate(emotion_probabilities)
        }
        valence = self._scalar(outputs[2])
        arousal = self._scalar(outputs[3])
        return {
            "provider": "cv4ed_affect_2026",
            "model": self.model_path.name,
            "expression": self._INDEX_TO_CLASS[label_index],
            "label": self._INDEX_TO_CLASS[label_index],
            "confidence": round(float(emotion_probabilities[label_index]), 6),
            "scores": scores,
            "valence": round(valence, 6),
            "arousal": round(arousal, 6),
            "epistemic": {},
        }

    def _preprocess(self, face_bgr: Any) -> Any:
        # Matches cv4ed-affect-2026/src/inference/run_hsemotion.py.
        face = self._cv2.resize(face_bgr, (224, 224))
        face = face.astype(self._numpy.float32) / 255.0
        face[:, :, 0] = (face[:, :, 0] - 0.485) / 0.229
        face[:, :, 1] = (face[:, :, 1] - 0.456) / 0.224
        face[:, :, 2] = (face[:, :, 2] - 0.406) / 0.225
        return face.transpose(2, 0, 1)[self._numpy.newaxis, ...]

    @staticmethod
    def _scalar(value: Any) -> float:
        try:
            return float(value.reshape(-1)[0])
        except (AttributeError, IndexError, TypeError, ValueError):
            return 0.0

    @staticmethod
    def _softmax(values: Any) -> list[float]:
        values = [float(value) for value in values]
        if not values:
            return []
        maximum = max(values)
        exponentials = [pow(2.718281828, value - maximum) for value in values]
        total = sum(exponentials) or 1.0
        return [value / total for value in exponentials]
