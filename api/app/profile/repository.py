"""Database queries about profile versions. Every query is limited to one user."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile.models import ProfileVersion


async def approved(db: AsyncSession, user_id: uuid.UUID) -> ProfileVersion | None:
    statement = select(ProfileVersion).where(
        ProfileVersion.user_id == user_id, ProfileVersion.status == "approved"
    )
    return (await db.scalars(statement)).one_or_none()


async def latest_number(db: AsyncSession, user_id: uuid.UUID) -> int:
    number = await db.scalar(
        select(func.max(ProfileVersion.version_no)).where(ProfileVersion.user_id == user_id)
    )
    return int(number or 0)


async def versions(db: AsyncSession, user_id: uuid.UUID) -> Sequence[ProfileVersion]:
    statement = (
        select(ProfileVersion)
        .where(ProfileVersion.user_id == user_id)
        .order_by(ProfileVersion.version_no.desc())
    )
    return (await db.scalars(statement)).all()


async def get(db: AsyncSession, user_id: uuid.UUID, version_id: uuid.UUID) -> ProfileVersion | None:
    statement = select(ProfileVersion).where(
        ProfileVersion.user_id == user_id, ProfileVersion.id == version_id
    )
    return (await db.scalars(statement)).one_or_none()


async def add(
    db: AsyncSession,
    user_id: uuid.UUID,
    facts: list[dict[str, Any]] | None,
    source_file_id: uuid.UUID | None,
) -> None:
    """Makes a new version the one in use. `facts` of None records that there is no
    approved profile any more (after undoing the first approval)."""
    await db.execute(
        update(ProfileVersion)
        .where(ProfileVersion.user_id == user_id, ProfileVersion.status == "approved")
        .values(status="superseded")
    )
    db.add(
        ProfileVersion(
            user_id=user_id,
            version_no=await latest_number(db, user_id) + 1,
            status="approved" if facts is not None else "superseded",
            facts=facts or [],
            source_file_id=source_file_id,
            approved_at=datetime.now(UTC) if facts is not None else None,
        )
    )
    await db.flush()
