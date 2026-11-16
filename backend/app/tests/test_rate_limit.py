"""Rate limiter tests — verifies fail-open behavior when Redis is
unreachable, per core/rate_limit.py.
"""

import pytest
from redis.asyncio import Redis

from app.core.rate_limit import enforce_rate_limit


async def test_rate_limit_fails_open_without_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """enforce_rate_limit must swallow a Redis outage and allow the request
    rather than raising, per its documented contract.

    The client is pointed at a port nothing listens on, so the test is
    deterministic whether or not a real Redis happens to be running (a live
    Redis would otherwise keep a persistent counter across test runs)."""
    dead_redis = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.3)
    monkeypatch.setattr("app.core.rate_limit.get_redis", lambda: dead_redis)
    try:
        for _ in range(3):  # > max_attempts: would raise if it were counting
            await enforce_rate_limit("rl:test:unreachable", max_attempts=1, window_seconds=60)
    finally:
        await dead_redis.aclose()
