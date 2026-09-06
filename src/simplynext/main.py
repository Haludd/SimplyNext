"""FastAPI application factory and command-line entry point."""

from __future__ import annotations

from asyncio import Semaphore
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from simplynext import __version__
from simplynext.api.lattice_websocket import lattice_socket
from simplynext.api.middleware import RequestBodyLimitMiddleware
from simplynext.api.routes import api_router, health_router
from simplynext.config import Settings, get_settings
from simplynext.lattice_runtime import (
    LatticeTranslationEngine,
    build_lattice_translation_engine,
)
from simplynext.observability import MetricsRegistry, configure_logging
from simplynext.runtime import RuntimeServices
from simplynext.sessions import EphemeralSessionStore


def create_app(
    settings: Settings | None = None,
    *,
    lattice_translation: LatticeTranslationEngine | None = None,
) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    metrics = (
        lattice_translation.metrics
        if lattice_translation is not None
        else MetricsRegistry()
    )
    lattice_engine = lattice_translation or build_lattice_translation_engine(
        runtime_settings,
        metrics,
    )
    sessions = EphemeralSessionStore(
        ttl_seconds=runtime_settings.session_ttl_seconds,
        max_sessions=runtime_settings.max_active_sessions,
        websocket_path_template=(
            f"{runtime_settings.api_prefix}/sessions/{{session_id}}/lattices"
        ),
        max_lattice_message_bytes=runtime_settings.gloss_lattice_max_message_bytes,
        max_lattices_per_session=runtime_settings.max_lattices_per_session,
        max_lattices_per_minute=runtime_settings.max_lattices_per_minute,
        max_lattices_per_minute_global=runtime_settings.max_lattices_per_minute_global,
    )
    services = RuntimeServices(
        settings=runtime_settings,
        sessions=sessions,
        lattice_translation=lattice_engine,
        agent_graph=lattice_engine.agent_graph,
        metrics=metrics,
        agent_slots=Semaphore(runtime_settings.max_concurrent_agent_runs),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.services = services
        yield
        await sessions.purge_expired()

    application = FastAPI(
        title="SimplyNext Backend",
        version=__version__,
        summary="Uncertainty-aware GlossLattice translation service",
        lifespan=lifespan,
    )
    application.state.services = services
    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=runtime_settings.http_max_body_bytes,
    )
    if runtime_settings.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(runtime_settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )
    application.include_router(health_router)
    application.include_router(api_router, prefix=runtime_settings.api_prefix)

    @application.websocket(f"{runtime_settings.api_prefix}/sessions/{{session_id}}/lattices")
    async def stream_lattices(websocket: WebSocket, session_id: UUID) -> None:
        await lattice_socket(websocket, session_id)

    return application


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "simplynext.main:app",
        host=settings.host,
        port=settings.port,
        log_config=None,
        ws_max_size=settings.gloss_lattice_max_message_bytes,
        workers=1,
    )
