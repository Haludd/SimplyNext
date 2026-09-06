"""Small, dependency-free temporal classifier interface for stage ⑤.

This is intentionally a trainable prototype model, not a claim that the demo
already has a useful ASL/SgSL model.  It pools variable-length feature
sequences into mean, endpoint-change, and motion summaries, then compares each
sequence with a learned class prototype.  A real small GRU/TCN can replace the
implementation without changing the top-k/calibration contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence


Vector = Sequence[float]


def _pool(sequence: Sequence[Vector]) -> list[float]:
    if not sequence:
        return []
    width = len(sequence[0])
    values = [[float(value) for value in row[:width]] for row in sequence]
    if any(len(row) != width for row in values):
        raise ValueError("all feature vectors in a sequence must have equal width")
    mean = [sum(row[index] for row in values) / len(values) for index in range(width)]
    delta = [values[-1][index] - values[0][index] for index in range(width)]
    motion = [
        sum(abs(values[row][index] - values[row - 1][index]) for row in range(1, len(values)))
        / max(len(values) - 1, 1)
        for index in range(width)
    ]
    return mean + delta + motion


def _distance(first: Vector, second: Vector) -> float:
    return math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(first, second)))


@dataclass
class TemperatureCalibrator:
    temperature: float = 1.0
    fitted: bool = False

    def fit(
        self,
        logits_and_labels: Iterable[tuple[dict[str, float], str]],
    ) -> float:
        rows = list(logits_and_labels)
        if not rows:
            raise ValueError("calibration requires validation predictions")
        candidates = [0.25 + index * 0.05 for index in range(76)]
        best_temperature = self.temperature
        best_loss = float("inf")
        for temperature in candidates:
            loss = 0.0
            for logits, label in rows:
                probabilities = _softmax(logits, temperature)
                loss -= math.log(max(probabilities.get(label, 1e-12), 1e-12))
            loss /= len(rows)
            if loss < best_loss:
                best_loss = loss
                best_temperature = temperature
        self.temperature = best_temperature
        self.fitted = True
        return best_loss


def _softmax(logits: dict[str, float], temperature: float) -> dict[str, float]:
    if not logits:
        return {}
    scale = max(float(temperature), 1e-6)
    maximum = max(logits.values())
    exponentials = {
        label: math.exp((value - maximum) / scale)
        for label, value in logits.items()
    }
    total = sum(exponentials.values()) or 1.0
    return {label: value / total for label, value in exponentials.items()}


class TemporalPrototypeClassifier:
    """Trainable closed-vocabulary sequence classifier with top-k output."""

    def __init__(self, *, refusal_threshold: float = 0.65) -> None:
        self.prototypes: dict[str, list[float]] = {}
        self.refusal_threshold = refusal_threshold
        self.calibrator = TemperatureCalibrator()

    @property
    def fitted(self) -> bool:
        return bool(self.prototypes)

    def fit(self, samples: Iterable[tuple[str, Sequence[Vector]]]) -> None:
        grouped: dict[str, list[list[float]]] = {}
        for label, sequence in samples:
            pooled = _pool(sequence)
            if not pooled:
                continue
            grouped.setdefault(label, []).append(pooled)
        if not grouped:
            raise ValueError("training requires at least one non-empty labelled sequence")
        self.prototypes = {
            label: [
                sum(row[index] for row in rows) / len(rows)
                for index in range(len(rows[0]))
            ]
            for label, rows in grouped.items()
        }

    def predict(self, sequence: Sequence[Vector], *, top_k: int = 5) -> dict[str, Any]:
        if not self.fitted:
            return {
                "top_k_glosses": [],
                "class_scores": {},
                "confidence": 0.0,
                "provenance": "unresolved",
                "refused": True,
                "calibrated": self.calibrator.fitted,
            }
        pooled = _pool(sequence)
        if not pooled or any(len(pooled) != len(prototype) for prototype in self.prototypes.values()):
            return {
                "top_k_glosses": [],
                "class_scores": {},
                "confidence": 0.0,
                "provenance": "unresolved",
                "refused": True,
                "calibrated": self.calibrator.fitted,
            }
        logits = {
            label: -_distance(pooled, prototype)
            for label, prototype in self.prototypes.items()
        }
        scores = _softmax(logits, self.calibrator.temperature)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        hypotheses = [
            {
                "rank": rank,
                "gloss_id": label,
                "gloss": label,
                "score": round(score, 6),
                "confidence": round(score, 6),
            }
            for rank, (label, score) in enumerate(ordered[:max(1, top_k)], start=1)
        ]
        confidence = hypotheses[0]["confidence"] if hypotheses else 0.0
        accepted = self.calibrator.fitted and confidence >= self.refusal_threshold
        return {
            "top_k_glosses": hypotheses,
            "class_scores": {label: round(score, 6) for label, score in scores.items()},
            "confidence": confidence,
            "provenance": "classifier_high_confidence" if accepted else "unresolved",
            "refused": not accepted,
            "calibrated": self.calibrator.fitted,
        }

    def calibrate(self, validation: Iterable[tuple[str, Sequence[Vector]]]) -> float:
        rows: list[tuple[dict[str, float], str]] = []
        for label, sequence in validation:
            pooled = _pool(sequence)
            if not pooled:
                continue
            logits = {
                candidate: -_distance(pooled, prototype)
                for candidate, prototype in self.prototypes.items()
            }
            rows.append((logits, label))
        return self.calibrator.fit(rows)

    def reliability_report(
        self,
        validation: Iterable[tuple[str, Sequence[Vector]]],
        *,
        bins: int = 10,
    ) -> dict[str, Any]:
        """Return data for the PLN/T4.3 reliability curve and refusal metric."""
        rows: list[tuple[float, bool, bool]] = []
        for label, sequence in validation:
            result = self.predict(sequence, top_k=1)
            hypotheses = result["top_k_glosses"]
            if not hypotheses:
                continue
            confidence = float(result["confidence"])
            correct = hypotheses[0]["gloss"] == label
            rows.append((confidence, correct, bool(result["refused"])))
        buckets: list[dict[str, Any]] = []
        for index in range(max(1, bins)):
            lower = index / max(1, bins)
            upper = (index + 1) / max(1, bins)
            selected = [row for row in rows if lower <= row[0] < upper or (index == bins - 1 and row[0] == upper)]
            buckets.append({
                "lower": round(lower, 4),
                "upper": round(upper, 4),
                "count": len(selected),
                "mean_confidence": round(sum(row[0] for row in selected) / len(selected), 6)
                if selected else 0.0,
                "accuracy": round(sum(row[1] for row in selected) / len(selected), 6)
                if selected else 0.0,
            })
        refused = [row for row in rows if row[2]]
        return {
            "temperature": self.calibrator.temperature,
            "calibrated": self.calibrator.fitted,
            "refusal_threshold": self.refusal_threshold,
            "sample_count": len(rows),
            "refusal_rate": round(len(refused) / len(rows), 6) if rows else 0.0,
            "refusal_precision": round(
                sum(not row[1] for row in refused) / len(refused), 6
            ) if refused else 0.0,
            "bins": buckets,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "prototypes": self.prototypes,
            "refusal_threshold": self.refusal_threshold,
            "temperature": self.calibrator.temperature,
            "calibrated": self.calibrator.fitted,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TemporalPrototypeClassifier":
        classifier = cls(refusal_threshold=float(value.get("refusal_threshold", 0.65)))
        classifier.prototypes = {
            str(label): [float(number) for number in values]
            for label, values in (value.get("prototypes") or {}).items()
        }
        classifier.calibrator.temperature = float(value.get("temperature", 1.0))
        classifier.calibrator.fitted = bool(value.get("calibrated", False))
        return classifier

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "TemporalPrototypeClassifier":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
