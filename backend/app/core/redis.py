"""Redis client (PRD Ch3.5 — session caching, rate limiting, queue management).

A single lazily-created connection pool is shared across the app. Callers
that use Redis for non-critical concerns (rate limiting) must tolerate the
client being unreachable — see `core/rate_limit.py`.
"""

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)
