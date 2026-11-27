from collections.abc import AsyncIterator

import httpx
import pytest

from app.core.errors import AppError
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

    # Routes that exist only inside this test, to trigger each kind of error.
    @app.get("/test/expected")
    async def expected() -> None:
        raise AppError("risky_job", "This job looks like a scam.", status_code=409)

    @app.get("/test/validate")
    async def validate(count: int) -> int:
        return count

    @app.get("/test/crash")
    async def crash() -> None:
        raise RuntimeError("secret detail: hidden-value")

    async with running_client(app) as test_client:
        yield test_client


async def test_expected_error_uses_the_one_shape(client: httpx.AsyncClient) -> None:
    response = await client.get("/test/expected")

    assert response.status_code == 409
    assert response.json() == {
        "detail": {"code": "risky_job", "message": "This job looks like a scam."}
    }


async def test_unknown_address_uses_the_one_shape(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/nothing-here")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "not_found"


async def test_wrong_method_uses_the_one_shape(client: httpx.AsyncClient) -> None:
    response = await client.post("/health")

    assert response.status_code == 405
    assert response.json()["detail"]["code"] == "method_not_allowed"
    assert response.headers["allow"] == "GET"


async def test_validation_error_names_field_without_echoing_value(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/test/validate", params={"count": "hidden-value"})

    detail = response.json()["detail"]
    assert response.status_code == 422
    assert detail["code"] == "validation_error"
    assert detail["fields"][0]["field"] == "count"
    assert "hidden-value" not in response.text


async def test_unexpected_error_is_hidden_from_caller_and_logs(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    from app.core.logging import configure_logging

    configure_logging("INFO")

    response = await client.get("/test/crash")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "internal_error"
    assert "hidden-value" not in response.text
    assert response.headers["x-request-id"]
    output = capsys.readouterr().out
    assert "unhandled_error" in output
    assert "RuntimeError" in output
    assert "hidden-value" not in output


async def test_safe_request_id_is_reused(client: httpx.AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-Id": "abc12345-from-proxy"})

    assert response.headers["x-request-id"] == "abc12345-from-proxy"


async def test_unsafe_request_id_is_replaced(client: httpx.AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-Id": "bad id {with} braces"})

    assert response.headers["x-request-id"] != "bad id {with} braces"
    assert len(response.headers["x-request-id"]) == 32
