"""Dependency-free HTTP adapter for the Flutter API client."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from .emotion import EmotionAnalysisError, EmotionDependenciesMissing
from .models import PayloadValidationError, SignSequencePayload
from .service import SignBridgeBackend


MAX_BODY_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BODY_BYTES = 2 * 1024 * 1024


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def create_server(host: str, port: int, service: SignBridgeBackend) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        backend = service

        def _send(self, status: HTTPStatus, body: dict[str, Any]) -> None:
            # A 204 response must not contain a response body. This matters for
            # the browser's CORS preflight before it uploads a JPEG snapshot.
            encoded = b"" if status == HTTPStatus.NO_CONTENT else _json_bytes(body)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            if encoded:
                self.wfile.write(encoded)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send(HTTPStatus.NO_CONTENT, {})

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                stored = self.backend.store.count() if self.backend.store else 0
                self._send(
                    HTTPStatus.OK,
                    {"status": "ok", "service": "signbridge-backend", "stored_sequences": stored},
                )
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/v1/emotions/analyze":
                self._analyze_emotion()
                return
            if self.path != "/v1/sign-sequences/analyze":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY_BYTES:
                    raise PayloadValidationError("request body size is invalid")
                raw = self.rfile.read(length)
                value = json.loads(raw.decode("utf-8"))
                payload = SignSequencePayload.from_dict(value)
                result = self.backend.analyze(payload)
            except (UnicodeDecodeError, json.JSONDecodeError, PayloadValidationError) as error:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_payload", "detail": str(error)},
                )
                return
            except Exception as error:  # keep server errors JSON-shaped for the client
                self._send(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "analysis_failed", "detail": str(error)},
                )
                return
            self._send(HTTPStatus.OK, result)

        def _analyze_emotion(self) -> None:
            content_type = self.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_content_type", "detail": "send a JPEG or PNG image"},
                )
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_IMAGE_BODY_BYTES:
                    raise EmotionAnalysisError("image body size is invalid")
                result = self.backend.analyze_emotion(self.rfile.read(length))
            except EmotionDependenciesMissing as error:
                self._send(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "deepface_unavailable", "detail": str(error)},
                )
                return
            except (ValueError, EmotionAnalysisError) as error:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_image", "detail": str(error)},
                )
                return
            except Exception as error:  # keep model errors JSON-shaped for the browser
                self._send(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "emotion_analysis_failed", "detail": str(error)},
                )
                return
            self._send(HTTPStatus.OK, result)

        def log_message(self, format: str, *args: Any) -> None:
            # Keep the demo terminal readable; callers can wrap the server for structured logs.
            return

    return ThreadingHTTPServer((host, port), Handler)
