"""Migrations apply to the database, can be reversed, and match the models."""

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.config import Settings
from app.db.session import create_engine


async def vector_extension_version(settings: Settings) -> str | None:
    engine = create_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            version: str | None = await connection.scalar(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            return version
    finally:
        await engine.dispose()


async def test_head_migration_enables_vector(test_settings: Settings) -> None:
    assert await vector_extension_version(test_settings) is not None


def test_migrations_downgrade_and_upgrade_again(alembic_config: Config) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_models_and_migrations_agree(alembic_config: Config) -> None:
    # Raises if a model has changes that no migration creates.
    command.check(alembic_config)
