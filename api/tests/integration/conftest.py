"""Setup for tests that use a real PostgreSQL and Redis (never mocks of the database)."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import ConfigError, Settings, load_settings
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.db.session import create_engine
from app.main import create_app
from tests.conftest import make_settings, running_client

API_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    try:
        loaded = load_settings()
    except ConfigError as error:
        pytest.fail(str(error), pytrace=False)
    if loaded.test_database_url is None or loaded.test_redis_url is None:
        pytest.fail(
            "Integration tests need TEST_DATABASE_URL and TEST_REDIS_URL (see api/.env.example).",
            pytrace=False,
        )
    database_url = loaded.test_database_url.get_secret_value()
    # Safety catch: these tests delete data, so they only run against a database named *_test.
    if not str(make_url(database_url).database).endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must point to a database whose name ends in _test.")
    return make_settings(database_url, loaded.test_redis_url.get_secret_value())


@pytest.fixture(scope="session")
def alembic_config(test_settings: Settings) -> Config:
    config = Config(str(API_DIR / "alembic.ini"))
    config.attributes["database_url"] = test_settings.database_url.get_secret_value()
    return config


@pytest.fixture(scope="session")
def migrated_database(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")


async def empty_everything(settings: Settings) -> None:
    engine = create_engine(settings.database_url.get_secret_value())
    async with engine.begin() as connection:
        tables = (
            await connection.scalars(
                text(
                    "SELECT quote_ident(tablename) FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
        ).all()
        if tables:
            await connection.execute(text(f"TRUNCATE {', '.join(tables)} CASCADE"))
    await engine.dispose()

    redis = create_redis(settings.redis_url.get_secret_value())
    await redis.flushdb()
    await redis.aclose()


@pytest.fixture(autouse=True)
def clean_state(test_settings: Settings, migrated_database: None) -> None:
    """Empty every table and the test Redis database before each test."""
    # Synchronous on purpose, so it also works for the synchronous migration tests.
    asyncio.run(empty_everything(test_settings), loop_factory=new_event_loop)


@pytest.fixture
async def client(test_settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    async with running_client(create_app(test_settings)) as test_client:
        yield test_client
