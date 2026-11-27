"""Async SQLAlchemy engine and session factory. Creating the engine does not connect."""

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
