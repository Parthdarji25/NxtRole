"""Command-line tools:  uv run python -m app.cli <command>   (--help lists them)."""

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable, Coroutine
from pathlib import Path
from typing import Any

import psycopg
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.auth import admin
from app.config import ENV_FILE, SETUP_HINT, ConfigError, Settings, load_settings
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.db.session import create_engine
from app.health.service import CHECK_TIMEOUT_SECONDS, ping_redis
from app.setup_local import setup_local

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


async def check_database_user(settings: Settings) -> str:
    """The API's own user must not be able to skip row-level security (D-039)."""
    engine = create_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            unlimited = await connection.scalar(
                text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")
            )
    finally:
        await engine.dispose()
    if unlimited:
        raise RuntimeError(f"DATABASE_URL uses an unlimited database user. {SETUP_HINT}")
    return "limited, as it should be"


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
    for name, secret in (
        ("MIGRATION_DATABASE_URL", settings.migration_database_url),
        ("JWT_SECRET", settings.jwt_secret),
    ):
        print(f"  {name} = {'set (hidden)' if secret else 'MISSING'}")
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
    if results[0]:
        results.append(await run_check("database user", check_database_user, settings))
    if settings.jwt_secret is None or settings.migration_database_url is None:
        print(f"  [FAIL] sign-in settings are missing. {SETUP_HINT}")
        results.append(False)
    if all(results):
        print("All checks passed.")
        return 0
    print("Some checks failed.")
    return 1


def run_setup_local(env_file: Path = ENV_FILE) -> int:
    try:
        done = setup_local(env_file)
    except ConfigError as error:
        print(error)
        return 1
    except psycopg.Error as error:
        # Only the error type is shown: driver messages can include connection details.
        print(f"The database could not be changed ({type(error).__name__}).")
        print(f"         {CONTAINER_HINT}")
        return 1
    for line in done:
        print(f"  [ OK ] {line}")
    print("Next:  uv run alembic upgrade head")
    return 0


def run_account_command(command: str, session_id: str | None) -> int:
    try:
        settings = load_settings()
        terminal = admin.Terminal()
        actions: dict[str, Callable[[], Coroutine[Any, Any, None]]] = {
            "create-owner": lambda: admin.create_owner(settings, terminal),
            "reset-password": lambda: admin.reset_password(settings, terminal),
            "list-sessions": lambda: admin.list_sessions(settings, terminal),
            "revoke-sessions": lambda: admin.revoke_sessions(settings, terminal, session_id),
        }
        asyncio.run(actions[command](), loop_factory=new_event_loop)
    except (ConfigError, admin.CommandError) as error:
        print(error)
        return 1
    except ProgrammingError:
        print("The database tables are missing. Run:  uv run alembic upgrade head")
        return 1
    except OperationalError as error:
        print(f"The database could not be reached ({type(error).__name__}).")
        print(f"         {CONTAINER_HINT}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Nothing was changed.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="NxtRole command-line tools.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-config", help="show settings and test the database and Redis")
    commands.add_parser(
        "setup-local", help="create the app's database user and signing secret on this computer"
    )
    commands.add_parser("create-owner", help="create your account (asks in the terminal)")
    commands.add_parser("reset-password", help="set a new password and recovery code")
    commands.add_parser("list-sessions", help="show the devices that are signed in")
    revoke = commands.add_parser("revoke-sessions", help="sign out devices")
    revoke.add_argument("--session", help="only this one (the id shown by list-sessions)")
    args = parser.parse_args(argv)

    if args.command == "check-config":
        return asyncio.run(check_config(), loop_factory=new_event_loop)
    if args.command == "setup-local":
        return run_setup_local()
    return run_account_command(args.command, getattr(args, "session", None))


if __name__ == "__main__":
    sys.exit(main())
