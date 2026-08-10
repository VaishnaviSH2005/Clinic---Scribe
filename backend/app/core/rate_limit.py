"""Fixed-window rate limiting backed by Redis (PRD Ch16.3 / Ch20 — brute
force protection on login, password reset, and refresh).

Fails open (logs a warning and allows the request) if Redis is unreachable,
so an infrastructure outage never blocks authentication entirely — this is
a deliberate availability trade-off for a security control that has a
second layer of defense (account lockout is out of scope for Version 1;
Argon2id + short-lived tokens remain in effect regardless).
"""

from redis.exceptions import RedisError

from app.core.exceptions import AppError
from app.core.logging import logger
from app.core.redis import get_redis


class RateLimitExceededError(AppError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


async def enforce_rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    """Raises RateLimitExceededError if `key` has been hit more than
    `max_attempts` times within `window_seconds`. Call after a failed
    attempt (login) or before a sensitive action (password reset request).
    """
    redis = get_redis()
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
    except RedisError:
        logger.warning("Rate limiter unavailable (Redis unreachable) — allowing request.", extra={"route": key})
        return

    if count > max_attempts:
        raise RateLimitExceededError(
            "Too many attempts. Please try again later.", error_code="RATE_LIMIT_EXCEEDED"
        )


async def reset_rate_limit(key: str) -> None:
    redis = get_redis()
    try:
        await redis.delete(key)
    except RedisError:
        logger.warning("Rate limiter unavailable (Redis unreachable) — skip reset.", extra={"route": key})
