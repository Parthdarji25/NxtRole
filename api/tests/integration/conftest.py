"""Setup for tests that use a real PostgreSQL and Redis (never mocks of the database)."""

import asyncio
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.auth import passwords
from app.config import ConfigError, Settings, load_settings
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.db.roles import APP_ROLE
from app.db.session import create_engine
from app.main import create_app
from app.setup_local import connect, ensure_login_role
from tests.conftest import make_settings, running_client

API_DIR = Path(__file__).resolve().parents[2]
TEST_ROLE = "nxtrole_app_test"


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
    owner_url = loaded.test_database_url.get_secret_value()
    owner = make_url(owner_url)
    # Safety catch: these tests delete data, so they only run against a database named *_test.
    if not str(owner.database).endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must point to a database whose name ends in _test.")
    # The app under test connects as a limited user, as it does in real use.
    password = secrets.token_hex(24)
    ensure_login_role(owner, TEST_ROLE, password)
    app_url = owner.set(username=TEST_ROLE, password=password)
    return make_settings(
        app_url.render_as_string(hide_password=False),
        loaded.test_redis_url.get_secret_value(),
        migration_database_url=SecretStr(owner_url),
    )


@pytest.fixture(scope="session")
def alembic_config(test_settings: Settings) -> Config:
    config = Config(str(API_DIR / "alembic.ini"))
    config.attributes["database_url"] = test_settings.require_migration_database_url()
    return config


@pytest.fixture(scope="session")
def migrated_database(alembic_config: Config, test_settings: Settings) -> None:
    command.upgrade(alembic_config, "head")
    # The test user receives exactly the rights the migrations give the app's user.
    owner = make_url(test_settings.require_migration_database_url())
    with connect(owner) as connection:
        connection.execute(
            sql.SQL("GRANT {} TO {}").format(sql.Identifier(APP_ROLE), sql.Identifier(TEST_ROLE))
        )


async def empty_everything(settings: Settings) -> None:
    engine = create_engine(settings.require_migration_database_url())
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


@pytest.fixture
def quick_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real settings take 0.3 seconds a hash. Tests of the sign-in rules use light
    ones; the real ones are checked in tests/unit/test_passwords_and_tokens.py."""
    monkeypatch.setattr(
        passwords, "HASHER", PasswordHasher(time_cost=1, memory_cost=8_192, parallelism=1)
    )
    passwords._dummy_hash.cache_clear()
