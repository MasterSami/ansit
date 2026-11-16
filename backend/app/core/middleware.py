"""Request context: request IDs, access log line and HTTP metrics (pure ASGI)."""

import re
import time
import uuid

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger
from app.core.metrics import HTTP_LATENCY, HTTP_REQUESTS

log = get_logger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_QUIET_PATHS = frozenset({"/healthz", "/readyz", "/metrics"})


def _request_id_from(headers: Headers) -> str:
    incoming = headers.get(REQUEST_ID_HEADER)
    if incoming and _VALID_REQUEST_ID.fullmatch(incoming):
        return incoming
    return str(uuid.uuid4())


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id_from(Headers(scope=scope))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        status = 500
        started = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - started
            route = scope.get("route")
            # Route template, not the raw path, keeps label cardinality bounded.
            route_label = getattr(route, "path", "unmatched")
            method = scope["method"]
            HTTP_REQUESTS.labels(method, route_label, str(status)).inc()
            HTTP_LATENCY.labels(method, route_label).observe(elapsed)
            if scope["path"] not in _QUIET_PATHS:
                log.info(
                    "http_request",
                    method=method,
                    path=scope["path"],
                    status=status,
                    duration_ms=round(elapsed * 1000, 2),
                )
            structlog.contextvars.clear_contextvars()
