from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from fastapi import Request
from starlette.requests import Request as StarletteRequest

from app.core.client_ip import client_ip, ip_hint
from app.core.concurrency import ensure_version
from app.core.errors import AppError
from app.core.pagination import decode_cursor, encode_cursor
from app.core.rate_limit import count_in_window, enforce_rate_limit
from app.core.redis import create_redis
from app.main import create_app
from tests.conftest import (
    make_settings,
    running_client,
    unreachable_database_url,
    unreachable_redis_url,
)


def request_from(host: str, forwarded: str | None = None) -> StarletteRequest:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
    return StarletteRequest({"type": "http", "headers": headers, "client": (host, 5000)})


@pytest.mark.parametrize(
    ("trusted", "forwarded", "expected"),
    [
        # No trusted forwarder: the header is ignored completely.
        (0, "203.0.113.9", "10.0.0.1"),
        # One trusted forwarder: its entry is the rightmost; the visitor's invention is not used.
        (1, "1.1.1.1, 203.0.113.9", "203.0.113.9"),
        (2, "203.0.113.9, 198.51.100.2", "203.0.113.9"),
        (1, "not-an-address", "10.0.0.1"),
        (1, None, "10.0.0.1"),
    ],
)
def test_client_address_only_believes_our_forwarders(
    trusted: int, forwarded: str | None, expected: str
) -> None:
    assert client_ip(request_from("10.0.0.1", forwarded), trusted) == expected


def test_ip_hint_shortens_the_address() -> None:
    assert ip_hint("203.0.113.57") == "203.0.113.0/24"
    assert ip_hint("2001:db8:abcd:12::1") == "2001:db8:abcd::/48"
    assert ip_hint("unknown") is None


def test_cursor_survives_a_round_trip() -> None:
    when, row_id = datetime(2026, 11, 27, 4, 5, 6, 789, tzinfo=UTC), uuid4()

    assert decode_cursor(encode_cursor(when, row_id)) == (when, row_id)


@pytest.mark.parametrize("bad", ["", "abc", "!!!!", "bm90fGF8Y3Vyc29y", "MjAyNi0xMS0yN3x4"])
def test_a_damaged_cursor_is_a_plain_error(bad: str) -> None:
    with pytest.raises(AppError) as error:
        decode_cursor(bad)

    assert (error.value.code, error.value.status_code) == ("validation_error", 422)


def test_old_version_is_a_conflict() -> None:
    ensure_version(3, 3)
    with pytest.raises(AppError) as error:
        ensure_version(4, 3)

    assert (error.value.code, error.value.status_code) == ("conflict", 409)
    assert error.value.extra == {"current_version": 4}


async def test_rate_limit_lets_requests_pass_when_redis_is_down() -> None:
    redis = create_redis(unreachable_redis_url())

    assert await count_in_window(redis, "key", 60) is None
    await enforce_rate_limit(redis, "key", limit=0, window_seconds=60)
    await redis.aclose()


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(make_settings(unreachable_database_url(), unreachable_redis_url()))

    @app.post("/test/echo")
    async def echo(request: Request) -> int:
        return len(await request.body())

    async with running_client(app) as test_client:
        yield test_client


async def test_normal_body_passes_unchanged(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/echo", content=b"x" * 2000)

    assert response.json() == 2000


async def test_oversized_body_is_refused(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/echo", content=b"x" * 1_000_001)

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "too_large"


async def test_oversized_body_without_a_declared_length_is_refused(
    client: httpx.AsyncClient,
) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        for _ in range(11):
            yield b"x" * 100_000

    response = await client.post("/test/echo", content=chunks())

    assert response.status_code == 413
