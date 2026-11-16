"""FastAPI application factory."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import Settings, get_settings
from app.core.dependencies import ExternalDeps
from app.core.logging import configure_logging, get_logger
from app.core.metrics import READY
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.core.readiness import Readiness, StartupTask, run_startup_tasks

log = get_logger(__name__)


def create_app(
    settings: Settings | None = None,
    startup_tasks: Sequence[StartupTask] | None = None,
) -> FastAPI:
    """Build the app. `startup_tasks` (model loaders) are registered here from Phase 2 on."""
    settings = settings or get_settings()
    tasks = list(startup_tasks or [])
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        READY.set(0)
        app.state.deps = ExternalDeps.from_settings(settings)
        # Background task: /healthz answers while models load; /readyz stays 503 until done.
        loader = asyncio.create_task(run_startup_tasks(tasks, app.state.readiness))
        log.info("app_starting", env=settings.app_env, version=settings.app_version)
        try:
            yield
        finally:
            loader.cancel()
            with suppress(asyncio.CancelledError):
                await loader
            await app.state.deps.aclose()
            log.info("app_stopped")

    app = FastAPI(
        title="Ansit API",
        version=settings.app_version,
        description="Identifies the surah, ayah and reciter from a short Quran recitation clip.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.readiness = Readiness()
    app.state.deps = ExternalDeps()

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            expose_headers=[REQUEST_ID_HEADER],
        )
    # Added last so it is outermost: every response carries a request ID.
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    return app
