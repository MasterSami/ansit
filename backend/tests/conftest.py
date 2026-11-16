from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import httpx
import pytest
from asgi_lifespan import LifespanManager

from app.core.config import Settings
from app.core.readiness import StartupTask
from app.main import create_app


def make_settings(**overrides: object) -> Settings:
    """Settings isolated from the developer's `.env` and process environment."""
    return Settings(_env_file=None, app_env="test", **overrides)  # type: ignore[arg-type]


@asynccontextmanager
async def running_client(
    settings: Settings | None = None,
    startup_tasks: Sequence[StartupTask] | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings or make_settings(), startup_tasks)
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with running_client() as c:
        yield c
