"""Shared test setup."""

import asyncio
import secrets
import socket
import tempfile
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from app.config import Settings
from app.core.loop import new_event_loop

SETTING_NAMES = (
    "APP_ENV",
    "LOG_LEVEL",
    "DATABASE_URL",
    "REDIS_URL",
    "TEST_DATABASE_URL",
    "TEST_REDIS_URL",
    "MIGRATION_DATABASE_URL",
    "JWT_SECRET",
    "LOGIN_RATE_PER_MINUTE",
    "TRUSTED_PROXY_COUNT",
    "GROQ_API_KEY",
    "GROQ_ZDR_CONFIRMED_ON",
    "AI_MAIN_MODEL",
    "AI_SMALL_MODEL",
    "AI_JUDGE_MODEL",
    "AI_REQUESTS_PER_MINUTE",
    "AI_REQUESTS_PER_DAY",
    "AI_TOKENS_PER_MINUTE",
    "AI_TOKENS_PER_DAY",
    "STORAGE_DIR",
)


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    # Use the same event loop as the app (needed by psycopg on Windows).
    return {"app": new_event_loop}


@pytest.fixture
def no_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove NxtRole settings from the environment so a test controls them fully."""
    for name in SETTING_NAMES:
        monkeypatch.delenv(name, raising=False)


def unused_port() -> int:
    """A local port with nothing listening on it, to imitate a stopped service."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def unreachable_database_url() -> str:
    return f"postgresql+psycopg://nobody:not-a-real-password@127.0.0.1:{unused_port()}/none_test"


def unreachable_redis_url() -> str:
    return f"redis://127.0.0.1:{unused_port()}/0"


TEST_STORAGE_DIR = Path(tempfile.mkdtemp(prefix="nxtrole-test-uploads-"))

# A new signing secret for every test run.
TEST_JWT_SECRET = secrets.token_urlsafe(48)


def make_settings(database_url: str, redis_url: str, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": "test",
        "database_url": SecretStr(database_url),
        "redis_url": SecretStr(redis_url),
        "jwt_secret": SecretStr(TEST_JWT_SECRET),
        # Never the folder that holds real uploads.
        "storage_dir": TEST_STORAGE_DIR,
    }
    return Settings(_env_file=None, **(values | overrides))


@asynccontextmanager
async def running_client(
    app: FastAPI, base_url: str = "http://test"
) -> AsyncIterator[httpx.AsyncClient]:
    """The app with its start-up and shutdown run, called without opening a network port."""
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
            yield client
