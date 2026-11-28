"""Counting requests in Redis: "no more than N in this many seconds"."""

from dataclasses import dataclass

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.errors import AppError

log = structlog.get_logger("nxtrole.rate_limit")


@dataclass(frozen=True)
class Window:
    count: int
    reset_seconds: int


async def count_in_window(redis: Redis, key: str, window_seconds: int) -> Window | None:
    """Adds one to the counter. Returns None when Redis cannot be reached.

    The window starts with the first request and ends `window_seconds` later.
    """
    try:
        async with redis.pipeline(transaction=True) as pipeline:
            pipeline.set(key, 0, ex=window_seconds, nx=True)
            pipeline.incr(key)
            pipeline.ttl(key)
            _, count, ttl = await pipeline.execute()
    except (RedisError, OSError) as error:
        log.warning("rate_limit_unavailable", error_type=type(error).__name__)
        return None
    return Window(count=int(count), reset_seconds=max(int(ttl), 1))


async def enforce_rate_limit(redis: Redis, key: str, limit: int, window_seconds: int) -> None:
    """Raises `rate_limited` over the limit. Lets the request pass if Redis is down:
    the database lockout still protects sign-in (E-62)."""
    window = await count_in_window(redis, key, window_seconds)
    if window is None or window.count <= limit:
        return
    raise AppError(
        "rate_limited",
        f"Too many attempts. Try again in {window.reset_seconds} seconds.",
        status_code=429,
        headers={
            "Retry-After": str(window.reset_seconds),
            "RateLimit-Limit": str(limit),
            "RateLimit-Remaining": "0",
            "RateLimit-Reset": str(window.reset_seconds),
        },
        extra={"retry_after_seconds": window.reset_seconds},
    )
