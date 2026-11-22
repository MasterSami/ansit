from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import RedisError

from app.core.ratelimit import RedisRateLimiter


@pytest.mark.asyncio
async def test_redis_failure_uses_local_rate_limit_fallback() -> None:
    pipeline = MagicMock()
    pipeline.execute = AsyncMock(side_effect=RedisError("unavailable"))
    redis = MagicMock()
    redis.pipeline.return_value = pipeline
    limiter = RedisRateLimiter(redis, limit=1, clock=lambda: 120.0)

    first = await limiter.hit("ip:client")
    second = await limiter.hit("ip:client")

    assert first.allowed
    assert not second.allowed
    assert second.retry_after == 60
