"""Stops password guessing (D-050).

Redis counts wrong attempts per email-and-address pair (locks at 5) and per email (locks at
20), so a stranger who guesses wrong cannot lock the owner out of their own network, and an
email without an account is treated exactly like one with an account. The database keeps its
own count on the user, which takes over if Redis is down.
"""

import hashlib
from datetime import timedelta

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.rate_limit import count_in_window

PAIR_LIMIT = 5
ACCOUNT_LIMIT = 20
WINDOW = timedelta(minutes=15)
WINDOW_SECONDS = int(WINDOW.total_seconds())

log = structlog.get_logger("nxtrole.lockout")


def _subject(email: str) -> str:
    # The address itself is never used as a key name.
    return hashlib.sha256(email.casefold().encode()).hexdigest()[:32]


def _keys(email: str, ip: str) -> tuple[str, str]:
    subject = _subject(email)
    return f"{subject}:{ip}", subject


async def locked_seconds(redis: Redis, email: str, ip: str) -> int | None:
    """Seconds left on a lock, 0 if there is none, None if Redis cannot be reached."""
    try:
        remaining = [await redis.ttl(f"auth:lock:{key}") for key in _keys(email, ip)]
    except (RedisError, OSError) as error:
        log.warning("lockout_unavailable", error_type=type(error).__name__)
        return None
    # Redis answers -2 for "no such key".
    return max(0, *(int(seconds) for seconds in remaining))


async def record_failure(redis: Redis, email: str, ip: str) -> int | None:
    """Counts a wrong attempt. Returns the length of the lock it caused (0 for none), or
    None if Redis cannot be reached."""
    locked = 0
    for key, limit in zip(_keys(email, ip), (PAIR_LIMIT, ACCOUNT_LIMIT), strict=True):
        window = await count_in_window(redis, f"auth:fail:{key}", WINDOW_SECONDS)
        if window is None:
            return None
        if window.count >= limit:
            try:
                await redis.set(f"auth:lock:{key}", 1, ex=WINDOW_SECONDS)
                await redis.delete(f"auth:fail:{key}")
            except (RedisError, OSError) as error:
                log.warning("lockout_unavailable", error_type=type(error).__name__)
                return None
            locked = WINDOW_SECONDS
    return locked


async def clear_after_success(redis: Redis, email: str, ip: str) -> None:
    """A correct password forgets the earlier mistakes."""
    try:
        await redis.delete(*(f"auth:fail:{key}" for key in _keys(email, ip)))
    except (RedisError, OSError) as error:
        log.warning("lockout_unavailable", error_type=type(error).__name__)


async def unlock(redis: Redis, email: str) -> None:
    """Removes every lock and count for an email (used after a password reset)."""
    try:
        keys = [key async for key in redis.scan_iter(f"auth:*:{_subject(email)}*")]
        if keys:
            await redis.delete(*keys)
    except (RedisError, OSError) as error:
        log.warning("lockout_unavailable", error_type=type(error).__name__)
