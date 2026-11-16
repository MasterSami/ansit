"""Ops endpoints: liveness, readiness and Prometheus metrics."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from app.core.dependencies import ExternalDeps
from app.core.metrics import render_metrics
from app.core.readiness import ComponentState, Readiness

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    components: dict[str, ComponentState]
    dependencies: dict[str, bool]


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness: the process is up and serving."""
    return HealthResponse()


@router.get(
    "/readyz",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
)
async def readyz(request: Request, response: Response) -> ReadyResponse:
    """Readiness: startup tasks (model loading) finished and stores are reachable."""
    readiness: Readiness = request.app.state.readiness
    deps: ExternalDeps = request.app.state.deps
    dependencies = await deps.check()
    ready = readiness.ready and all(dependencies.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if ready else "not_ready",
        components=dict(readiness.components),
        dependencies=dependencies,
    )


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
