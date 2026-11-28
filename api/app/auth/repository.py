"""Database queries about sign-ins (refresh tokens). Every query is limited to one user."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.auth.models import RefreshToken


@dataclass(frozen=True)
class SessionSummary:
    """One signed-in device."""

    family_id: UUID
    signed_in_at: datetime
    last_used_at: datetime
    user_agent: str | None
    ip_hint: str | None


async def user_id_for_token(session: AsyncSession, token_hash: str) -> UUID | None:
    """Works before anyone is signed in: the database function returns only an id."""
    found: UUID | None = await session.scalar(select(func.auth_user_id_for_token(token_hash)))
    return found


async def lock_token(session: AsyncSession, user_id: UUID, token_hash: str) -> RefreshToken | None:
    """Reads the token and holds it until the transaction ends, so two requests cannot both
    use it."""
    statement = (
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.token_hash == token_hash)
        .with_for_update()
    )
    return (await session.scalars(statement)).one_or_none()


async def is_signed_in(session: AsyncSession, user_id: UUID, family_id: UUID) -> bool:
    found = await session.scalar(
        select(
            exists().where(
                RefreshToken.user_id == user_id,
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > func.now(),
            )
        )
    )
    return bool(found)


async def revoke_family(session: AsyncSession, user_id: UUID, family_id: UUID) -> int:
    """Ends one sign-in. Returns how many tokens were still alive."""
    result = await session.scalars(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=func.now())
        .returning(RefreshToken.id)
    )
    return len(result.all())


async def revoke_all(
    session: AsyncSession, user_id: UUID, *, keep_family: UUID | None = None
) -> None:
    statement = update(RefreshToken).where(
        RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
    )
    if keep_family is not None:
        statement = statement.where(RefreshToken.family_id != keep_family)
    await session.execute(statement.values(revoked_at=func.now()))


async def delete_old(session: AsyncSession, user_id: UUID) -> None:
    """Housekeeping: tokens that expired more than a day ago can never be used again."""
    await session.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < func.now() - timedelta(days=1),
        )
    )


async def active_sessions(session: AsyncSession, user_id: UUID) -> Sequence[SessionSummary]:
    """One row per signed-in device, the most recently used first."""
    first = aliased(RefreshToken)
    signed_in_at = (
        select(func.min(first.created_at))
        .where(first.user_id == user_id, first.family_id == RefreshToken.family_id)
        .scalar_subquery()
    )
    # Each live sign-in has exactly one token that has not been used yet: its newest.
    statement = (
        select(
            RefreshToken.family_id,
            signed_in_at,
            RefreshToken.created_at,
            RefreshToken.user_agent,
            RefreshToken.ip_hint,
        )
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.used_at.is_(None),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > func.now(),
        )
        .order_by(RefreshToken.created_at.desc())
    )
    return [SessionSummary(*row) for row in (await session.execute(statement)).all()]
