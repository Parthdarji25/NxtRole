"""Tiny rows for tests, written by the database owner. Test code only, never part of the app."""

import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import (
    AiUsage,
    BackgroundJob,
    Event,
    File,
    IdempotencyKey,
    ProfileVersion,
    Proposal,
    RefreshToken,
    Rule,
    SearchPreferences,
    User,
)
from app.db.session import create_engine, create_session_factory


@asynccontextmanager
async def owner_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """A transaction as the database owner, who sees every row. Commits on success."""
    engine = create_engine(settings.require_migration_database_url())
    try:
        async with create_session_factory(engine).begin() as session:
            yield session
    finally:
        await engine.dispose()


async def one_row_in_every_table(settings: Settings, email: str) -> uuid.UUID:
    """A user with one row in each per-user table. Returns the user's id."""
    async with owner_session(settings) as session:
        user = User(email=email, password_hash="unused", recovery_code_hash="unused")
        session.add(user)
        await session.flush()
        later = datetime.now(UTC) + timedelta(days=1)
        session.add_all(
            [
                RefreshToken(
                    user_id=user.id,
                    family_id=uuid.uuid4(),
                    token_hash=secrets.token_hex(32),
                    expires_at=later,
                ),
                IdempotencyKey(
                    user_id=user.id,
                    key=secrets.token_hex(8),
                    request_hash="hash",
                    status_code=201,
                    response={},
                    expires_at=later,
                ),
                Proposal(
                    user_id=user.id,
                    kind="rename_profile",
                    target_type="profile",
                    target_id=user.id,
                    payload={},
                    created_by="test",
                ),
                Event(
                    user_id=user.id,
                    actor="you",
                    action="profile.name_changed",
                    target_type="profile",
                    target_id=user.id,
                ),
                File(
                    user_id=user.id,
                    kind="resume",
                    storage_path="unused",
                    original_name="unused.pdf",
                    content_type="application/pdf",
                    size_bytes=1,
                ),
                BackgroundJob(user_id=user.id, kind="profile_extract"),
                ProfileVersion(user_id=user.id, version_no=1, status="approved", facts=[]),
                SearchPreferences(user_id=user.id),
                Rule(user_id=user.id, kind="min_fixed_pay", value={}, origin="you"),
                AiUsage(user_id=user.id, day=date(2026, 11, 28), provider="groq", model="test"),
            ]
        )
        return user.id
