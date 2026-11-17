"""Fixed-window rate limiting, per client IP and per device id.

With Redis the counters are shared by every instance. Without it an in-process
limiter is used, which is only correct for a single instance.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger

log = get_logger(__name__)

WINDOW_SEC = 60


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after: int
    """Seconds until the current window ends."""


class RateLimiter(Protocol):
    async def hit(self, key: str) -> RateDecision:
        """Count one request for `key` and say whether it is allowed."""
        ...


def _window(now: float) -> tuple[int, int]:
    return int(now // WINDOW_SEC), max(1, int(WINDOW_SEC - now % WINDOW_SEC))


class MemoryRateLimiter:
    def __init__(self, limit: int, clock: Callable[[], float] = time.time) -> None:
        self.limit = limit
        self._clock = clock
        self._window = -1
        self._counts: dict[str, int] = {}

    async def hit(self, key: str) -> RateDecision:
        window, retry_after = _window(self._clock())
        if window != self._window:  # a new minute: forget the old counts
            self._window, self._counts = window, {}
        self._counts[key] = self._counts.get(key, 0) + 1
        return RateDecision(self._counts[key] <= self.limit, retry_after)


class RedisRateLimiter:
    def __init__(self, redis: Redis, limit: int, clock: Callable[[], float] = time.time) -> None:
        self.limit = limit
        self._redis = redis
        self._clock = clock

    async def hit(self, key: str) -> RateDecision:
        window, retry_after = _window(self._clock())
        name = f"ansit:rl:{key}:{window}"
        try:
            pipeline = self._redis.pipeline()
            pipeline.incr(name)
            pipeline.expire(name, WINDOW_SEC * 2)
            count, _ = await pipeline.execute()
        except (RedisError, OSError) as exc:
            # The limiter being down must not take identification down with it.
            log.warning("rate_limiter_unavailable", error=type(exc).__name__)
            return RateDecision(True, retry_after)
        return RateDecision(int(count) <= self.limit, retry_after)
