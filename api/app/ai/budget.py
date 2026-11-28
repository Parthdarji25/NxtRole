"""Keeps the app inside the provider's free limits (D-033).

Limits belong to the provider account, so they are counted in Redis for everyone together:
tokens and requests in the last minute and in the day, and a pause after the provider says
"too many". If Redis cannot be reached, calls go ahead and the provider enforces the limits.
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import Settings

MINUTE = 60.0
DAY_KEPT_SECONDS = 48 * 3600
# A rough, deliberately high estimate: about 3.5 characters make one token.
CHARACTERS_PER_TOKEN = 3.5

log = structlog.get_logger("nxtrole.ai.budget")


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARACTERS_PER_TOKEN) + 1


@dataclass(frozen=True)
class Go:
    reservation: str | None


@dataclass(frozen=True)
class Wait:
    seconds: float


@dataclass(frozen=True)
class Exhausted:
    """This model cannot be used until the day's allowance or its pause ends."""

    seconds: float


class Budget:
    def __init__(
        self, redis: Redis, settings: Settings, clock: Callable[[], float] = time.time
    ) -> None:
        self.redis = redis
        self.settings = settings
        self.clock = clock

    def _day_key(self, model: str) -> str:
        day = datetime.fromtimestamp(self.clock(), UTC).date().isoformat()
        return f"ai:day:{model}:{day}"

    def _seconds_to_next_day(self) -> float:
        return 86_400 - (self.clock() % 86_400)

    async def _recent(self, window: str) -> list[tuple[str, float]]:
        """The calls booked in the last minute: ("id:tokens", time), oldest first."""
        entries: Any = await self.redis.zrange(window, 0, -1, withscores=True)
        return [(str(member), float(score)) for member, score in entries]

    async def blocked_for(self, model: str) -> float:
        """Seconds until the model may be tried, 0 if it may be now."""
        try:
            pause = await self.redis.ttl(f"ai:block:{model}")
            day = await self.redis.hgetall(self._day_key(model))
        except (RedisError, OSError) as error:
            log.warning("ai_budget_unavailable", error_type=type(error).__name__)
            return 0
        if int(pause) > 0:
            return float(pause)
        if (
            int(day.get("tokens", 0)) >= self.settings.ai_tokens_per_day
            or int(day.get("requests", 0)) >= self.settings.ai_requests_per_day
        ):
            return self._seconds_to_next_day()
        return 0

    async def acquire(self, model: str, tokens: int) -> Go | Wait | Exhausted:
        """Books `tokens` for one call, or says how long to wait."""
        blocked = await self.blocked_for(model)
        if blocked:
            return Exhausted(blocked)
        now = self.clock()
        window = f"ai:window:{model}"
        try:
            day = await self.redis.hgetall(self._day_key(model))
            if int(day.get("tokens", 0)) + tokens > self.settings.ai_tokens_per_day:
                return Exhausted(self._seconds_to_next_day())
            await self.redis.zremrangebyscore(window, 0, now - MINUTE)
            recent = await self._recent(window)
            used = sum(int(member.split(":")[1]) for member, _ in recent)
            too_many_tokens = used + tokens > self.settings.ai_tokens_per_minute
            too_many_requests = len(recent) >= self.settings.ai_requests_per_minute
            if recent and (too_many_tokens or too_many_requests):
                # Wait until the oldest call leaves the one-minute window.
                return Wait(max(0.5, recent[0][1] + MINUTE - now + 0.1))
            reservation = uuid.uuid4().hex
            await self.redis.zadd(window, {f"{reservation}:{tokens}": now})
            await self.redis.expire(window, int(MINUTE) * 2)
        except (RedisError, OSError) as error:
            log.warning("ai_budget_unavailable", error_type=type(error).__name__)
            return Go(None)
        return Go(reservation)

    async def settle(self, model: str, reservation: str | None, tokens: int) -> None:
        """Replaces the estimate with what the call really used, and counts the day."""
        window = f"ai:window:{model}"
        try:
            if reservation is not None:
                for member, booked_at in await self._recent(window):
                    if member.startswith(f"{reservation}:"):
                        await self.redis.zrem(window, member)
                        await self.redis.zadd(window, {f"{reservation}:{tokens}": booked_at})
            day = self._day_key(model)
            await self.redis.hincrby(day, "tokens", tokens)
            await self.redis.hincrby(day, "requests", 1)
            await self.redis.expire(day, DAY_KEPT_SECONDS)
        except (RedisError, OSError) as error:
            log.warning("ai_budget_unavailable", error_type=type(error).__name__)

    async def release(self, model: str, reservation: str | None) -> None:
        """Gives back the tokens booked for a call that the provider did not answer."""
        if reservation is None:
            return
        window = f"ai:window:{model}"
        try:
            for member, _ in await self._recent(window):
                if member.startswith(f"{reservation}:"):
                    await self.redis.zrem(window, member)
        except (RedisError, OSError) as error:
            log.warning("ai_budget_unavailable", error_type=type(error).__name__)

    async def pause(self, model: str, seconds: float) -> None:
        """The provider said "too many": leave this model alone for a while."""
        try:
            await self.redis.set(f"ai:block:{model}", 1, ex=max(1, int(seconds)))
        except (RedisError, OSError) as error:
            log.warning("ai_budget_unavailable", error_type=type(error).__name__)
