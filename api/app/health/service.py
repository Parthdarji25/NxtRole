"""Checks whether the services NxtRole depends on answer in time."""

import asyncio
from collections.abc import Awaitable
from typing import Any, Literal

import structlog
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

CheckResult = Literal["ok", "error"]
CHECK_TIMEOUT_SECONDS = 4.0

log = structlog.get_logger("nxtrole.health")


async def ping_database(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def ping_redis(redis: Redis) -> None:
    # redis-py types ping() as possibly synchronous; on the async client it is awaitable.
    pending: Any = redis.ping()
    await pending


async def _run(name: str, check: Awaitable[None]) -> CheckResult:
    try:
        await asyncio.wait_for(check, timeout=CHECK_TIMEOUT_SECONDS)
    except Exception as exc:
        # A failed check is an expected situation: report it, never crash.
        log.warning("health_check_failed", service=name, error_type=type(exc).__name__)
        return "error"
    return "ok"


async def check_services(engine: AsyncEngine, redis: Redis) -> dict[str, CheckResult]:
    database, cache = await asyncio.gather(
        _run("database", ping_database(engine)),
        _run("redis", ping_redis(redis)),
    )
    return {"database": database, "redis": cache}
