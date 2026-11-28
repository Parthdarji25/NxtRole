"""Starts the API for the browser tests:  uv run python -m tests.e2e_server

It builds a new, empty database of its own (never the development one), creates the test
accounts named in the E2E_* variables, and serves the API on port 8100. AI is a stand-in with
one scripted answer, so no request leaves this computer, and uploads go to a temporary
folder. Test code only.
"""

import asyncio
import json
import os
import secrets
import sys
import tempfile
from datetime import date
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy.engine import make_url

from app.auth import passwords
from app.config import ConfigError, Settings, load_settings
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.db.models import User
from app.db.roles import APP_ROLE
from app.db.session import create_engine, create_session_factory
from app.main import create_app
from app.setup_local import connect, ensure_login_role
from tests.ai_helpers import SYNTHETIC_ANSWER, FakeTransport

API_DIR = Path(__file__).resolve().parents[1]
PORT = 8100
ROLE = "nxtrole_app_e2e"
# Redis databases: 0 is development, 1 is pytest, 2 is this.
REDIS_NUMBER = 2


def prepare(storage: Path) -> Settings:
    base = load_settings()
    if base.test_database_url is None or base.test_redis_url is None:
        raise ConfigError("The browser tests need TEST_DATABASE_URL and TEST_REDIS_URL.")
    tests_url = make_url(base.test_database_url.get_secret_value())
    if not str(tests_url.database).endswith("_test"):
        raise ConfigError("TEST_DATABASE_URL must point to a database whose name ends in _test.")
    name = f"{str(tests_url.database).removesuffix('_test')}_e2e_test"
    owner = tests_url.set(database=name)

    # PostgreSQL's own "postgres" database always exists, so it is used to create ours.
    with connect(tests_url.set(database="postgres")) as connection:
        database = sql.Identifier(name)
        connection.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(database))
        connection.execute(sql.SQL("CREATE DATABASE {}").format(database))

    config = Config(str(API_DIR / "alembic.ini"))
    config.attributes["database_url"] = owner.render_as_string(hide_password=False)
    command.upgrade(config, "head")

    password = secrets.token_hex(24)
    ensure_login_role(owner, ROLE, password)
    with connect(owner) as connection:
        connection.execute(
            sql.SQL("GRANT {} TO {}").format(sql.Identifier(APP_ROLE), sql.Identifier(ROLE))
        )

    redis_url = make_url(base.test_redis_url.get_secret_value()).set(database=str(REDIS_NUMBER))
    app_url = owner.set(username=ROLE, password=password)
    return Settings(
        _env_file=None,
        app_env="test",
        log_level="WARNING",
        database_url=SecretStr(app_url.render_as_string(hide_password=False)),
        migration_database_url=SecretStr(owner.render_as_string(hide_password=False)),
        redis_url=SecretStr(redis_url.render_as_string(hide_password=False)),
        jwt_secret=SecretStr(secrets.token_urlsafe(48)),
        # Every browser test signs in, all from this computer.
        login_rate_per_minute=10_000,
        storage_dir=storage,
        # The stand-in AI needs no real key; these switch the AI features on.
        groq_api_key=SecretStr("browser-tests-only"),
        groq_zdr_confirmed_on=date(2026, 11, 1),
        ai_requests_per_minute=10_000,
        ai_requests_per_day=100_000,
        ai_tokens_per_minute=10_000_000,
        ai_tokens_per_day=100_000_000,
    )


async def seed(settings: Settings) -> None:
    redis = create_redis(settings.redis_url.get_secret_value())
    await redis.flushdb()
    await redis.aclose()

    password = os.environ["E2E_PASSWORD"]
    code = os.environ["E2E_RECOVERY_CODE"]
    engine = create_engine(settings.require_migration_database_url())
    async with create_session_factory(engine).begin() as session:
        for email in json.loads(os.environ["E2E_EMAILS"]):
            session.add(
                User(
                    email=email,
                    password_hash=await passwords.hash_password(password),
                    recovery_code_hash=await passwords.hash_recovery_code(code),
                )
            )
    await engine.dispose()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nxtrole-e2e-") as storage:
        try:
            settings = prepare(Path(storage))
        except ConfigError as error:
            print(error, file=sys.stderr)
            return 1
        asyncio.run(seed(settings), loop_factory=new_event_loop)
        uvicorn.run(
            create_app(settings, ai_transport=FakeTransport(SYNTHETIC_ANSWER)),
            host="127.0.0.1",
            port=PORT,
            loop="app.core.loop:new_event_loop",
            log_config=None,
            access_log=False,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
