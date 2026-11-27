"""The API must start and report problems when the database or Redis cannot be reached."""

from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import create_app
from tests.conftest import (
    make_settings,
    running_client,
    unreachable_database_url,
    unreachable_redis_url,
)


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(make_settings(unreachable_database_url(), unreachable_redis_url()))
    async with running_client(app) as test_client:
        yield test_client


@pytest.mark.parametrize("path", ["/health", "/api/health"])
async def test_health_is_alive_without_services(client: httpx.AsyncClient, path: str) -> None:
    response = await client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"


async def test_ready_reports_503_and_which_parts_failed(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health/ready")

    detail = response.json()["detail"]
    assert response.status_code == 503
    assert detail["code"] == "not_ready"
    assert detail["checks"] == {"database": "error", "redis": "error"}
    assert "not-a-real-password" not in response.text


@pytest.mark.parametrize(
    ("environment", "expected"), [("local", 200), ("production", 404), ("test", 404)]
)
async def test_api_description_is_only_published_locally(environment: str, expected: int) -> None:
    settings = make_settings(unreachable_database_url(), unreachable_redis_url())
    app = create_app(settings.model_copy(update={"app_env": environment}))

    async with running_client(app) as client:
        response = await client.get("/api/openapi.json")

    assert response.status_code == expected
