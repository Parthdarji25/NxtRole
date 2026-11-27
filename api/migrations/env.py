"""Alembic environment: runs migrations with the async database driver.

The database address comes from the app's settings, never from alembic.ini.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from app.config import ConfigError, get_settings
from app.core.loop import new_event_loop
from app.db.base import Base
from app.db.session import create_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def database_url() -> str:
    # Tests pass their own address (the test database) through config.attributes.
    override: str | None = config.attributes.get("database_url")
    if override:
        return override
    try:
        return get_settings().database_url.get_secret_value()
    except ConfigError as error:
        raise SystemExit(str(error)) from None


def run_migrations_offline() -> None:
    """Print the SQL instead of running it: uv run alembic upgrade head --sql"""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_engine(database_url())
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online(), loop_factory=new_event_loop)
