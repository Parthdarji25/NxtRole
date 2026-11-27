"""Redis client. Creating it does not connect; the first command does."""

from redis.asyncio import Redis

TIMEOUT_SECONDS = 2.0


def create_redis(url: str) -> Redis:
    return Redis.from_url(
        url,
        socket_connect_timeout=TIMEOUT_SECONDS,
        socket_timeout=TIMEOUT_SECONDS,
        decode_responses=True,
    )
