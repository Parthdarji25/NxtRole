"""Database queries about users. Every query names the user it is about."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


async def id_for_email(session: AsyncSession, email: str) -> UUID | None:
    """Works before anyone is signed in: the database function returns only an id."""
    found: UUID | None = await session.scalar(select(func.auth_user_id_for_email(email)))
    return found


async def get(session: AsyncSession, user_id: UUID, *, lock: bool = False) -> User | None:
    statement = select(User).where(User.id == user_id)
    if lock:
        statement = statement.with_for_update()
    return (await session.scalars(statement)).one_or_none()


async def record_failed_login(
    session: AsyncSession, user_id: UUID, threshold: int, window: timedelta
) -> datetime | None:
    """Counts a wrong password and locks the account at `threshold`, in one statement, so
    that attempts arriving at the same moment are all counted. Returns the lock's end."""
    now = func.now()
    attempts = case(
        (or_(User.last_failed_at.is_(None), User.last_failed_at < now - window), 1),
        else_=User.failed_logins + 1,
    )
    locked_until = await session.scalar(
        update(User)
        .where(User.id == user_id)
        .values(
            failed_logins=attempts,
            last_failed_at=now,
            locked_until=case((attempts >= threshold, now + window), else_=User.locked_until),
        )
        .returning(User.locked_until)
    )
    return locked_until


async def clear_failed_logins(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(failed_logins=0, last_failed_at=None, locked_until=None)
    )
