"""Proposals, history and undo under /api."""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.core.deps import CurrentUser
from app.core.pagination import DEFAULT_LIMIT, Cursor, Limit, Page
from app.history import repository, service

router = APIRouter(prefix="/api", tags=["history"])


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: datetime
    actor: str
    action: str
    target_type: str
    target_id: uuid.UUID
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    proposal_id: uuid.UUID | None
    undo_of: uuid.UUID | None
    undone_by: uuid.UUID | None
    note: str | None


class ProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    kind: str
    target_type: str
    target_id: uuid.UUID | None
    payload: dict[str, Any]
    status: str
    created_by: str
    decided_at: datetime | None


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The owner's corrected version of the proposal, if they changed it.
    edited_payload: dict[str, Any] | None = None


class Approved(BaseModel):
    proposal: ProposalOut
    event_id: uuid.UUID | None


class Undone(BaseModel):
    event_id: uuid.UUID


@router.get("/history", response_model=Page[EventOut])
async def history(
    current: CurrentUser,
    target_type: Annotated[str | None, Query(max_length=50)] = None,
    target_id: uuid.UUID | None = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> Page[EventOut]:
    rows, next_cursor = await repository.list_events(
        current.db, current.user.id, target_type, target_id, limit, cursor
    )
    return Page(items=[EventOut.model_validate(row) for row in rows], next_cursor=next_cursor)


@router.post("/events/{event_id}/undo", response_model=Undone)
async def undo(event_id: uuid.UUID, current: CurrentUser) -> Undone:
    event = await service.undo(current.db, current.user.id, event_id)
    return Undone(event_id=event.id)


@router.get("/proposals", response_model=Page[ProposalOut])
async def proposals(
    current: CurrentUser,
    status: Literal["pending", "applied", "rejected", "expired", "failed"] = "pending",
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> Page[ProposalOut]:
    rows, next_cursor = await repository.list_proposals(
        current.db, current.user.id, status, limit, cursor
    )
    return Page(items=[ProposalOut.model_validate(row) for row in rows], next_cursor=next_cursor)


@router.post("/proposals/{proposal_id}/approve", response_model=Approved)
async def approve(
    proposal_id: uuid.UUID, current: CurrentUser, body: Approval | None = None
) -> Approved:
    proposal, event = await service.approve(
        current.db, current.user.id, proposal_id, body.edited_payload if body else None
    )
    return Approved(
        proposal=ProposalOut.model_validate(proposal), event_id=event.id if event else None
    )


@router.post("/proposals/{proposal_id}/reject", response_model=ProposalOut)
async def reject(proposal_id: uuid.UUID, current: CurrentUser) -> ProposalOut:
    proposal = await service.reject(current.db, current.user.id, proposal_id)
    return ProposalOut.model_validate(proposal)
