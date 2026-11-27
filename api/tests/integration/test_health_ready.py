import httpx
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from tests.conftest import running_client, unreachable_database_url, unreachable_redis_url


async def test_ready_is_ok_when_database_and_redis_answer(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"database": "ok", "redis": "ok"}


async def test_ready_is_503_when_only_redis_is_down(test_settings: Settings) -> None:
    settings = test_settings.model_copy(update={"redis_url": SecretStr(unreachable_redis_url())})

    async with running_client(create_app(settings)) as client:
        response = await client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"]["checks"] == {"database": "ok", "redis": "error"}


async def test_ready_is_503_when_only_database_is_down(test_settings: Settings) -> None:
    settings = test_settings.model_copy(
        update={"database_url": SecretStr(unreachable_database_url())}
    )

    async with running_client(create_app(settings)) as client:
        response = await client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"]["checks"] == {"database": "error", "redis": "ok"}
