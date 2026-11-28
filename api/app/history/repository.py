"""Database queries about proposals and history. Every query is limited to one user."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import newest_first
from app.history.models import Event, Proposal


async def lock_event(db: AsyncSession, user_id: uuid.UUID, event_id: uuid.UUID) -> Event | None:
    statement = (
        select(Event).where(Event.user_id == user_id, Event.id == event_id).with_for_update()
    )
    return (await db.scalars(statement)).one_or_none()


async def list_events(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_type: str | None,
    target_id: uuid.UUID | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Event], str | None]:
    statement = select(Event).where(Event.user_id == user_id)
    if target_type is not None:
        statement = statement.where(Event.target_type == target_type)
    if target_id is not None:
        statement = statement.where(Event.target_id == target_id)
    return await newest_first(db, statement, Event.occurred_at, Event.id, limit, cursor)


async def lock_proposal(
    db: AsyncSession, user_id: uuid.UUID, proposal_id: uuid.UUID
) -> Proposal | None:
    statement = (
        select(Proposal)
        .where(Proposal.user_id == user_id, Proposal.id == proposal_id)
        .with_for_update()
    )
    return (await db.scalars(statement)).one_or_none()


async def list_proposals(
    db: AsyncSession, user_id: uuid.UUID, status: str, limit: int, cursor: str | None
) -> tuple[Sequence[Proposal], str | None]:
    statement = select(Proposal).where(Proposal.user_id == user_id, Proposal.status == status)
    return await newest_first(db, statement, Proposal.created_at, Proposal.id, limit, cursor)
