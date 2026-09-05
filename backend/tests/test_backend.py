from __future__ import annotations

import tempfile
import json
import threading
from urllib.request import Request, urlopen
import unittest
from pathlib import Path

from backend.signbridge_backend.http_api import create_server
from backend.signbridge_backend.models import PayloadValidationError, SignSequencePayload
from backend.signbridge_backend.service import SignBridgeBackend
from backend.signbridge_backend.store import SequenceStore


class FakeEmotionAnalyzer:
    def analyze(self, image_bytes: bytes) -> dict:
        assert image_bytes == b"fake-jpeg"
        return {
            "status": "ok",
            "dominant_emotion": "happy",
            "confidence": 0.86,
            "emotions": {"happy": 0.86, "neutral": 0.14},
            "model": "DeepFace",
        }


def payload(*, frame_count: int = 1) -> dict:
    frames = [
        {
            "timestamp": "2026-09-05T08:14:02.000Z",
            "tracking_confidence": 0.95,
            "hands": [],
            "face_expression": {"label": "neutral", "confidence": 0.9},
        }
        for _ in range(frame_count)
    ]
    return {
        "session_id": "session-test",
        "sequence_id": "sequence-test",
        "language": "ASL",
        "started_at": frames[0]["timestamp"],
        "ended_at": frames[-1]["timestamp"],
        "frame_count": frame_count,
        "lexicon_version": "2026-09-seed-2",
        "frames": frames,
    }


class BackendTests(unittest.TestCase):
    def test_validates_and_analyzes_no_signal(self) -> None:
        parsed = SignSequencePayload.from_dict(payload())
        result = SignBridgeBackend().analyze(parsed)
        self.assertEqual(result["status"], "no_signal")
        self.assertEqual(result["language"], "ASL")

    def test_rejects_frame_count_mismatch(self) -> None:
        value = payload()
        value["frame_count"] = 2
        with self.assertRaises(PayloadValidationError):
            SignSequencePayload.from_dict(value)

    def test_stores_the_sequence_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sequences.jsonl"
            service = SignBridgeBackend(store=SequenceStore(path))
            service.analyze(SignSequencePayload.from_dict(payload()))
            self.assertEqual(SequenceStore(path).count(), 1)

    def test_http_endpoint_matches_flutter_contract(self) -> None:
        server = create_server("127.0.0.1", 0, SignBridgeBackend())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            address = server.server_address
            request = Request(
                f"http://{address[0]}:{address[1]}/v1/sign-sequences/analyze",
                data=json.dumps(payload()).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(result["status"], "no_signal")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_emotion_endpoint_returns_deepface_result(self) -> None:
        server = create_server(
            "127.0.0.1",
            0,
            SignBridgeBackend(emotion_analyzer=FakeEmotionAnalyzer()),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            address = server.server_address
            request = Request(
                f"http://{address[0]}:{address[1]}/v1/emotions/analyze",
                data=b"fake-jpeg",
                headers={"Content-Type": "image/jpeg"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertEqual(result["dominant_emotion"], "happy")
            self.assertEqual(result["model"], "DeepFace")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
