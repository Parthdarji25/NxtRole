"""Command-line tools:  uv run python -m app.cli check-config

Later phases add more checks and commands (for example create-owner in Phase 4).
"""

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import ENV_FILE, ConfigError, Settings, load_settings
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.db.session import create_engine
from app.health.service import CHECK_TIMEOUT_SECONDS, ping_redis

CONTAINER_HINT = (
    "Are the containers running? From the repository root run:  wsl docker compose up -d\n"
    "         Then check them:  wsl docker compose ps   (see README, 'Troubleshooting')"
)


def describe_url(url: str) -> str:
    """Host, port and database only. The user name and password are never shown."""
    parsed = make_url(url)
    location = f"{parsed.host}:{parsed.port}"
    return f"{location}/{parsed.database}" if parsed.database else location


async def check_database(settings: Settings) -> str:
    engine = create_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            version = await connection.scalar(text("SHOW server_version"))
            vector = await connection.scalar(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
    finally:
        await engine.dispose()
    if vector is None:
        raise RuntimeError("connected, but migrations have not run: uv run alembic upgrade head")
    return f"PostgreSQL {version.split()[0]}, pgvector {vector}"


async def check_redis(settings: Settings) -> str:
    redis = create_redis(settings.redis_url.get_secret_value())
    try:
        await ping_redis(redis)
    finally:
        await redis.aclose()
    return "reachable"


async def run_check(
    name: str, check: Callable[[Settings], Awaitable[str]], settings: Settings
) -> bool:
    try:
        detail = await asyncio.wait_for(check(settings), timeout=CHECK_TIMEOUT_SECONDS + 2)
    except RuntimeError as error:
        print(f"  [FAIL] {name}: {error}")
        return False
    except Exception as error:
        # Only the error type is shown: driver messages can include connection details.
        print(f"  [FAIL] {name}: could not connect ({type(error).__name__}).")
        print(f"         {CONTAINER_HINT}")
        return False
    print(f"  [ OK ] {name}: {detail}")
    return True


async def check_config(env_file: Path | None = ENV_FILE) -> int:
    try:
        settings = load_settings(env_file)
    except ConfigError as error:
        print(error)
        return 1

    database_url = settings.database_url.get_secret_value()
    redis_url = settings.redis_url.get_secret_value()
    print("Settings")
    print(f"  APP_ENV       = {settings.app_env}")
    print(f"  LOG_LEVEL     = {settings.log_level}")
    print(f"  DATABASE_URL  = set (hidden), points to {describe_url(database_url)}")
    print(f"  REDIS_URL     = set (hidden), points to {describe_url(redis_url)}")
    for name, value in (
        ("TEST_DATABASE_URL", settings.test_database_url),
        ("TEST_REDIS_URL", settings.test_redis_url),
    ):
        state = "set (hidden)" if value else "not set (only needed to run tests)"
        print(f"  {name} = {state}")

    print("Connections")
    results = [
        await run_check("database", check_database, settings),
        await run_check("redis", check_redis, settings),
    ]
    if all(results):
        print("All checks passed.")
        return 0
    print("Some checks failed.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="NxtRole command-line tools.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-config", help="show settings and test the database and Redis")
    args = parser.parse_args(argv)

    if args.command == "check-config":
        return asyncio.run(check_config(), loop_factory=new_event_loop)
    return 2


if __name__ == "__main__":
    sys.exit(main())
