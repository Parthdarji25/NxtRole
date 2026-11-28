"""The database itself keeps one person's rows away from another (D-039, E-70)."""

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db.base import Base
from app.db.session import create_engine, create_session_factory, set_current_user
from tests.integration.factories import one_row_in_every_table

TABLES = sorted(Base.metadata.tables)


@pytest.fixture
async def app_sessions(test_settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Connections as the limited user the API uses."""
    engine = create_engine(test_settings.database_url.get_secret_value())
    yield create_session_factory(engine)
    await engine.dispose()


async def count(session: AsyncSession, table: str) -> int:
    # The table name comes from our own models, not from any input.
    return int(await session.scalar(text(f"SELECT count(*) FROM {table}")) or 0)  # noqa: S608


@pytest.mark.parametrize("table", TABLES)
async def test_rls_wrong_user_sees_nothing(
    table: str,
    test_settings: Settings,
    app_sessions: async_sessionmaker[AsyncSession],
) -> None:
    owner_of_rows = await one_row_in_every_table(test_settings, "first@example.com")
    other = await one_row_in_every_table(test_settings, "second@example.com")

    async with app_sessions.begin() as session:
        assert await count(session, table) == 0, "nobody signed in must see nothing"
    async with app_sessions.begin() as session:
        await set_current_user(session, uuid.uuid4())
        assert await count(session, table) == 0
    for user_id in (owner_of_rows, other):
        async with app_sessions.begin() as session:
            await set_current_user(session, user_id)
            assert await count(session, table) == 1, "a user sees exactly their own row"


async def test_every_table_has_row_level_security(
    app_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with app_sessions.begin() as session:
        unprotected = (
            await session.scalars(
                text(
                    "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace "
                    "AND relkind = 'r' AND relname <> 'alembic_version' AND NOT relrowsecurity"
                )
            )
        ).all()

    assert unprotected == []


async def test_the_setting_does_not_stay_on_a_reused_connection(
    test_settings: Settings, app_sessions: async_sessionmaker[AsyncSession]
) -> None:
    user_id = await one_row_in_every_table(test_settings, "first@example.com")
    async with app_sessions.begin() as session:
        await set_current_user(session, user_id)

    async with app_sessions.begin() as session:
        assert await count(session, "events") == 0


async def test_a_user_cannot_add_a_row_for_someone_else(
    test_settings: Settings, app_sessions: async_sessionmaker[AsyncSession]
) -> None:
    mine = await one_row_in_every_table(test_settings, "first@example.com")
    theirs = await one_row_in_every_table(test_settings, "second@example.com")

    with pytest.raises(ProgrammingError, match="row-level security"):
        async with app_sessions.begin() as session:
            await set_current_user(session, mine)
            await session.execute(
                text(
                    "INSERT INTO events (user_id, actor, action, target_type, target_id) "
                    "VALUES (:user, 'you', 'x', 'profile', :user)"
                ),
                {"user": theirs},
            )


@pytest.mark.parametrize(
    "statement",
    [
        # History is append-only, and the app cannot create or remove accounts.
        "UPDATE events SET action = 'changed'",
        "DELETE FROM events",
        "DELETE FROM users",
        "INSERT INTO users (email, password_hash, recovery_code_hash) VALUES ('a@b.com','x','x')",
        "DELETE FROM proposals",
        "ALTER TABLE users DISABLE ROW LEVEL SECURITY",
    ],
)
async def test_the_app_user_has_only_the_rights_it_needs(
    statement: str, app_sessions: async_sessionmaker[AsyncSession]
) -> None:
    with pytest.raises(ProgrammingError, match=r"permission denied|must be owner"):
        async with app_sessions.begin() as session:
            await session.execute(text(statement))


@pytest.mark.parametrize("email", ["FIRST@Example.com", "first@example.com"])
async def test_the_sign_in_lookup_ignores_capitals_and_returns_only_an_id(
    email: str, test_settings: Settings, app_sessions: async_sessionmaker[AsyncSession]
) -> None:
    user_id = await one_row_in_every_table(test_settings, "First@example.com")

    async with app_sessions.begin() as session:
        found = await session.scalar(
            text("SELECT auth_user_id_for_email(:email)"), {"email": email}
        )
        missing = await session.scalar(text("SELECT auth_user_id_for_email('no@example.com')"))

    assert (found, missing) == (user_id, None)
