"""Connections to external stores (Postgres, Redis) and their health checks."""

import asyncio
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)

CHECK_TIMEOUT_SEC = 1.0


@dataclass
class ExternalDeps:
    engine: AsyncEngine | None = None
    redis: Redis | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ExternalDeps":
        engine = (
            create_async_engine(settings.database_url, pool_pre_ping=True)
            if settings.database_url
            else None
        )
        redis = Redis.from_url(settings.redis_url) if settings.redis_url else None
        return cls(engine=engine, redis=redis)

    async def _check_database(self) -> None:
        assert self.engine is not None  # noqa: S101 - narrowed by caller
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def _check_redis(self) -> None:
        assert self.redis is not None  # noqa: S101 - narrowed by caller
        await self.redis.ping()

    async def check(self) -> dict[str, bool]:
        """Ping each configured store. Unconfigured stores are omitted."""
        checks = {}
        if self.engine is not None:
            checks["database"] = self._check_database()
        if self.redis is not None:
            checks["redis"] = self._check_redis()

        results: dict[str, bool] = {}
        for name, coro in checks.items():
            try:
                await asyncio.wait_for(coro, timeout=CHECK_TIMEOUT_SEC)
            except Exception as exc:
                results[name] = False
                log.warning("dependency_check_failed", dependency=name, error=type(exc).__name__)
            else:
                results[name] = True
        return results

    async def aclose(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
        if self.redis is not None:
            await self.redis.aclose()
