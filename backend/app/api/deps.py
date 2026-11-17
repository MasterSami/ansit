"""Shared request dependencies: loaded services, client identity, rate limiting."""

import re
from typing import Annotated

from fastapi import Depends, Header, Request

from app.api.errors import ApiError
from app.core.config import Settings
from app.core.metrics import RATE_LIMITED
from app.core.ratelimit import RateLimiter
from app.identify_service import IdentifyService
from app.matcher.index import QuranIndex
from app.services import Services

_DEVICE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_APP_VERSION = re.compile(r"^[A-Za-z0-9._+-]{1,32}$")


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


def get_index(services: Annotated[Services, Depends(get_services)]) -> QuranIndex:
    if services.index is None:
        raise ApiError(503, "not_ready", "The service is still starting.")
    return services.index


def get_identify_service(request: Request) -> IdentifyService:
    service: IdentifyService | None = getattr(request.app.state, "identify", None)
    if service is None:
        raise ApiError(503, "not_ready", "The service is still starting.")
    return service


def client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def device_id(x_device_id: Annotated[str | None, Header()] = None) -> str | None:
    """A client-chosen stable id. Ignored unless it looks like one."""
    return x_device_id if x_device_id and _DEVICE_ID.fullmatch(x_device_id) else None


def app_version(x_app_version: Annotated[str | None, Header()] = None) -> str | None:
    return x_app_version if x_app_version and _APP_VERSION.fullmatch(x_app_version) else None


async def enforce_rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    device: Annotated[str | None, Depends(device_id)],
) -> None:
    """Per IP and, when the client sends one, per device id."""
    limiter: RateLimiter = request.app.state.limiter
    scopes = [("ip", client_ip(request, settings))]
    if device is not None:
        scopes.append(("device", device))
    for scope, value in scopes:
        decision = await limiter.hit(f"{scope}:{value}")
        if not decision.allowed:
            RATE_LIMITED.labels(scope).inc()
            raise ApiError(
                429,
                "rate_limited",
                "Too many requests. Try again shortly.",
                {"Retry-After": str(decision.retry_after)},
            )
