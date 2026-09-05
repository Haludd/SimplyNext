"""Short-lived HTTP endpoints outside the landmark streaming loop."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from simplynext import __version__
from simplynext.contracts import (
    SessionCreateRequest,
    SessionCreateResponse,
    TranslationResult,
    UtteranceRequest,
)
from simplynext.runtime import RuntimeServices
from simplynext.sessions import (
    InvalidSessionToken,
    SessionExpired,
    SessionNotFound,
    SessionStoreError,
    TooManySessions,
)

health_router = APIRouter(tags=["service"])
api_router = APIRouter(tags=["translation"])
replay_router = APIRouter(tags=["development replay"])


def services_from_request(request: Request) -> RuntimeServices:
    services = request.app.state.services
    if not isinstance(services, RuntimeServices):
        raise RuntimeError("application services are not initialized")
    return services


@health_router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": "SimplyNext Backend",
        "version": __version__,
        "docs": "/docs",
    }


@health_router.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@health_router.get("/readyz")
async def readiness(request: Request, response: Response) -> dict[str, object]:
    services = services_from_request(request)
    metadata = services.translation.recognizer.metadata
    recognizer_ready = metadata.ready and metadata.calibrated
    assembler_ready = services.translation.assembler_ready
    landmark_stream_ready = recognizer_ready and assembler_ready
    lattice_stream_ready = assembler_ready
    ready = landmark_stream_ready or lattice_stream_ready
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    if not recognizer_ready and not assembler_ready:
        state = "recognizer_unconfigured"
    elif not assembler_ready:
        state = "caption_assembler_unconfigured"
    elif not recognizer_ready:
        state = "lattice_stream_ready"
    else:
        state = "ready"
    return {
        "status": state,
        "recognizer": asdict(metadata),
        "caption_assembler": {"ready": assembler_ready},
        "input_modes": {
            "gloss_lattice": {"ready": lattice_stream_ready},
            "landmarks": {"ready": landmark_stream_ready},
        },
    }


@health_router.get("/metrics")
async def metrics(request: Request) -> dict[str, object]:
    return services_from_request(request).metrics.snapshot()


@api_router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    payload: SessionCreateRequest,
    request: Request,
    response: Response,
) -> SessionCreateResponse:
    services = services_from_request(request)
    model_language = services.translation.model_language
    if model_language is not None and payload.language is not model_language:
        raise HTTPException(
            status_code=422,
            detail=f"this deployment is configured for {model_language.value}",
        )
    try:
        session = await services.sessions.create(payload)
    except TooManySessions as exc:
        raise _http_session_error(exc) from exc
    response.headers["Cache-Control"] = "no-store"
    services.metrics.increment("sessions_created")
    return session


@api_router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    services = services_from_request(request)
    token = _bearer_token(authorization)
    try:
        await services.sessions.delete(session_id, token)
    except SessionStoreError as exc:
        raise _http_session_error(exc) from exc
    services.metrics.increment("sessions_deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@replay_router.post("/utterances", response_model=TranslationResult)
async def translate_utterance(
    payload: UtteranceRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> TranslationResult:
    """Authenticated development-only replay seam for classified hypotheses."""

    services = services_from_request(request)
    token = _bearer_token(authorization)
    try:
        snapshot = await services.sessions.authenticate(payload.session_id, token)
    except SessionStoreError as exc:
        raise _http_session_error(exc) from exc
    if snapshot.language is not payload.language:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="payload language does not match the session",
        )
    services.metrics.increment("utterance_requests")
    return await services.translation.process_hypotheses(payload)


def _bearer_token(value: str | None) -> str:
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    scheme, separator, token = value.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )
    return token.strip()


def _http_session_error(exc: SessionStoreError) -> HTTPException:
    if isinstance(exc, InvalidSessionToken):
        code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, SessionNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, SessionExpired):
        code = status.HTTP_410_GONE
    elif isinstance(exc, TooManySessions):
        code = status.HTTP_429_TOO_MANY_REQUESTS
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=exc.message)
