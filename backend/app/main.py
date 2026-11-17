"""FastAPI application factory."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.formparsers import MultiPartParser

from app.api import feedback, health, identify, quran, reciters
from app.api.errors import install_error_handlers
from app.core.config import Settings, get_settings
from app.core.dependencies import ExternalDeps
from app.core.ephemeral import CandidateStore, MemoryCandidateStore, RedisCandidateStore
from app.core.logging import configure_logging, get_logger
from app.core.metrics import READY
from app.core.middleware import (
    REQUEST_ID_HEADER,
    BodySizeLimitMiddleware,
    RequestContextMiddleware,
)
from app.core.ratelimit import MemoryRateLimiter, RateLimiter, RedisRateLimiter
from app.core.readiness import Readiness, StartupTask, run_startup_tasks
from app.identify_service import IdentifyService
from app.services import Services, build_startup_tasks

log = get_logger(__name__)

# Room for the multipart envelope and the small form fields around the audio.
MULTIPART_OVERHEAD = 64 * 1024


def create_app(
    settings: Settings | None = None,
    startup_tasks: Sequence[StartupTask] | None = None,
    services: Services | None = None,
    limiter: RateLimiter | None = None,
) -> FastAPI:
    """Build the app.

    By default the index, models and gallery are loaded at startup as readiness
    tasks. Tests pass ready-made `services` (and `LOAD_MODELS=false`) instead.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)
    max_body = int(settings.max_upload_mb * 1024 * 1024) + MULTIPART_OVERHEAD
    # Uploads are capped at `max_body`, so letting the parser keep that much in
    # memory means an audio clip is never spooled to a temporary file on disk.
    MultiPartParser.spool_max_size = max(MultiPartParser.spool_max_size, max_body + 1)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        READY.set(0)
        deps = ExternalDeps.from_settings(settings)
        app.state.deps = deps
        loaded: Services = app.state.services

        if limiter is None:
            app.state.limiter = (
                RedisRateLimiter(deps.redis, settings.rate_limit_per_min)
                if deps.redis is not None
                else MemoryRateLimiter(settings.rate_limit_per_min)
            )
        candidates: CandidateStore = (
            RedisCandidateStore(deps.redis, settings.ambiguous_ttl_sec)
            if deps.redis is not None
            else MemoryCandidateStore(settings.ambiguous_ttl_sec)
        )
        service = IdentifyService(settings, loaded, candidates, deps.sessions)
        app.state.identify = service

        tasks = list(startup_tasks or [])
        if settings.load_models and services is None:
            tasks += build_startup_tasks(settings, loaded, deps.sessions)
        # Background task: /healthz answers while models load; /readyz stays 503 until done.
        loader = asyncio.create_task(run_startup_tasks(tasks, app.state.readiness))
        log.info("app_starting", env=settings.app_env, version=settings.app_version)
        try:
            yield
        finally:
            loader.cancel()
            with suppress(asyncio.CancelledError):
                await loader
            await service.drain()
            service.close()
            await deps.aclose()
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
    app.state.services = services or Services()
    app.state.limiter = limiter or MemoryRateLimiter(settings.rate_limit_per_min)
    install_error_handlers(app)

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_body)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            expose_headers=[REQUEST_ID_HEADER, "Retry-After"],
        )
    # Added last so it is outermost: every response carries a request ID.
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    app.include_router(identify.router)
    app.include_router(quran.router)
    app.include_router(reciters.router)
    app.include_router(feedback.router)
    return app
