"""Rate limiter tests — verifies fail-open behavior when Redis is
unreachable (no live Redis in this test environment) per core/rate_limit.py.
"""

from app.core.rate_limit import enforce_rate_limit


async def test_rate_limit_fails_open_without_redis() -> None:
    """Redis is not running in the test environment, so `redis.asyncio`
    calls will raise/timeout — enforce_rate_limit must swallow that and
    allow the request rather than raising, per its documented contract."""
    await enforce_rate_limit("rl:test:unreachable", max_attempts=1, window_seconds=60)
