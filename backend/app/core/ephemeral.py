"""Short-lived memory of an ambiguous result, for the "listen longer" follow-up.

What is kept: the word positions of the candidate locations, for a few minutes.
What is never kept: audio or transcript.
"""

import json
import time
from collections.abc import Callable
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger

log = get_logger(__name__)

Spans = list[tuple[int, int]]
"""Candidate locations as (first, last) global word positions."""


class CandidateStore(Protocol):
    async def put(self, identify_id: str, spans: Spans) -> None: ...

    async def get(self, identify_id: str) -> Spans | None: ...


class MemoryCandidateStore:
    def __init__(self, ttl_sec: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl_sec
        self._clock = clock
        self._items: dict[str, tuple[float, Spans]] = {}

    async def put(self, identify_id: str, spans: Spans) -> None:
        now = self._clock()
        self._items = {k: v for k, v in self._items.items() if v[0] > now}
        self._items[identify_id] = (now + self._ttl, spans)

    async def get(self, identify_id: str) -> Spans | None:
        item = self._items.get(identify_id)
        if item is None or item[0] <= self._clock():
            return None
        return item[1]


class RedisCandidateStore:
    def __init__(self, redis: Redis, ttl_sec: int) -> None:
        self._redis = redis
        self._ttl = ttl_sec

    async def put(self, identify_id: str, spans: Spans) -> None:
        try:
            await self._redis.set(f"ansit:amb:{identify_id}", json.dumps(spans), ex=self._ttl)
        except (RedisError, OSError) as exc:
            log.warning("candidate_store_unavailable", error=type(exc).__name__)

    async def get(self, identify_id: str) -> Spans | None:
        try:
            raw = await self._redis.get(f"ansit:amb:{identify_id}")
        except (RedisError, OSError) as exc:
            log.warning("candidate_store_unavailable", error=type(exc).__name__)
            return None
        if raw is None:
            return None
        return [(int(a), int(b)) for a, b in json.loads(raw)]
