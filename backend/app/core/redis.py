"""Redis client (PRD Ch3.5 — session caching, rate limiting, queue management).

A single lazily-created connection pool is shared across the app. Callers
that use Redis for non-critical concerns (rate limiting) must tolerate the
client being unreachable — see `core/rate_limit.py`.
"""

import inspect
from collections.abc import Awaitable
from functools import lru_cache
from typing import TypeVar

from redis.asyncio import Redis

from app.core.config import settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


@lru_cache
def get_redis_bytes() -> Redis:
    """Binary-safe client (no string decoding) for raw audio frames and pub/sub."""
    return Redis.from_url(settings.redis_url, decode_responses=False)


T = TypeVar("T")


async def resolve(value: "Awaitable[T] | T") -> T:
    """redis-py types its async client's commands as `Awaitable[T] | T` (one stub for
    both the sync and async clients); with the async client they are always awaitable."""
    return await value if inspect.isawaitable(value) else value  # type: ignore[return-value]
