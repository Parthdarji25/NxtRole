"""Async SQLAlchemy engine and session factory. Creating the engine does not connect."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

CONNECT_TIMEOUT_SECONDS = 3


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        # Check a pooled connection is alive before using it (free databases drop idle ones).
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def set_current_user(session: AsyncSession, user_id: UUID) -> None:
    """Tells the database whose rows this transaction may see (row-level security, D-039).

    The setting ends with the transaction, so a reused connection starts with nobody.
    """
    await session.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": str(user_id)}
    )
