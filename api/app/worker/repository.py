"""Database queries about background jobs. Every query is limited to one user."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker.models import BackgroundJob

ACTIVE = ("queued", "running")


async def get(
    db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, kind: str
) -> BackgroundJob | None:
    statement = (
        select(BackgroundJob)
        .where(
            BackgroundJob.user_id == user_id,
            BackgroundJob.id == job_id,
            BackgroundJob.kind == kind,
        )
        .with_for_update()
    )
    return (await db.scalars(statement)).one_or_none()


async def active(db: AsyncSession, user_id: uuid.UUID, kind: str) -> BackgroundJob | None:
    statement = (
        select(BackgroundJob)
        .where(
            BackgroundJob.user_id == user_id,
            BackgroundJob.kind == kind,
            BackgroundJob.state.in_(ACTIVE),
        )
        .with_for_update()
    )
    return (await db.scalars(statement)).one_or_none()


async def latest(db: AsyncSession, user_id: uuid.UUID, kind: str) -> BackgroundJob | None:
    statement = (
        select(BackgroundJob)
        .where(BackgroundJob.user_id == user_id, BackgroundJob.kind == kind)
        .order_by(BackgroundJob.created_at.desc(), BackgroundJob.id.desc())
        .limit(1)
    )
    return (await db.scalars(statement)).one_or_none()
