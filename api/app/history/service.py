"""Applying a change, approving or rejecting a proposal, and undoing (FR-099, FR-138).

Each function works inside the caller's transaction: the change and its history row are
saved together or not at all.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.history import repository
from app.history.changes import CHANGES, TARGETS, Change, not_found
from app.history.models import Event, Proposal

YOU = "you"


def check_payload(change: Change, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return change.payload.model_validate(payload).model_dump(mode="json")
    except ValidationError as error:
        fields = [
            {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
            for item in error.errors(include_input=False, include_url=False)
        ]
        raise AppError(
            "validation_error",
            "Some of the information sent is not valid.",
            status_code=422,
            extra={"fields": fields},
        ) from None


async def apply_change(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    target_id: uuid.UUID,
    payload: dict[str, Any],
    *,
    expected_version: int | None,
    actor: str = YOU,
    proposal_id: uuid.UUID | None = None,
    stale_code: str = "conflict",
) -> Event | None:
    """Makes the change and writes its history row. Returns None if nothing would change."""
    change = CHANGES[kind]
    values = check_payload(change, payload)
    target = TARGETS[change.target_type]
    now = await target.read(db, user_id, target_id)
    if expected_version is not None and now.version != expected_version:
        raise AppError(
            stale_code,
            "This was changed somewhere else. Reload to see the latest, then try again.",
            status_code=409,
            extra={"current_version": now.version},
        )
    before = {name: now.values[name] for name in values}
    if before == values:
        return None
    await target.write(db, user_id, target_id, values)
    event = Event(
        user_id=user_id,
        actor=actor,
        action=change.action,
        target_type=change.target_type,
        target_id=target_id,
        before=before,
        after=values,
        proposal_id=proposal_id,
    )
    db.add(event)
    await db.flush()
    return event


async def undo(db: AsyncSession, user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
    """Puts back what an event changed, unless something newer would be overwritten."""
    event = await repository.lock_event(db, user_id, event_id)
    if event is None:
        raise not_found()
    if event.undone_by is not None:
        raise AppError("already_undone", "That change was already undone.", status_code=409)
    target = TARGETS.get(event.target_type)
    if target is None or event.before is None or event.after is None:
        raise AppError("undo_blocked", "That change cannot be undone.", status_code=409)

    now = await target.read(db, user_id, event.target_id)
    changed_since = [name for name, value in event.after.items() if now.values.get(name) != value]
    if changed_since:
        raise AppError(
            "undo_blocked",
            "It was changed again after this, so undoing would overwrite the newer change. "
            "Undo the newer change first.",
            status_code=409,
            extra={"blocked_by": changed_since},
        )
    await target.write(db, user_id, event.target_id, event.before)
    reverse = Event(
        user_id=user_id,
        actor=YOU,
        action=event.action,
        target_type=event.target_type,
        target_id=event.target_id,
        before=event.after,
        after=event.before,
        undo_of=event.id,
    )
    db.add(reverse)
    await db.flush()
    event.undone_by = reverse.id
    await db.flush()
    return reverse


async def propose(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    target_id: uuid.UUID,
    payload: dict[str, Any],
    *,
    created_by: str,
) -> Proposal:
    """Records a change that waits for the owner. Nothing else changes. Used by agents and
    rules from Phase 9 on; there is no web address that creates proposals."""
    change = CHANGES[kind]
    values = check_payload(change, payload)
    now = await TARGETS[change.target_type].read(db, user_id, target_id)
    proposal = Proposal(
        user_id=user_id,
        kind=kind,
        target_type=change.target_type,
        target_id=target_id,
        payload=values,
        base_version=now.version,
        created_by=created_by,
    )
    db.add(proposal)
    await db.flush()
    await db.refresh(proposal)
    return proposal


async def _pending(db: AsyncSession, user_id: uuid.UUID, proposal_id: uuid.UUID) -> Proposal:
    proposal = await repository.lock_proposal(db, user_id, proposal_id)
    if proposal is None:
        raise not_found()
    if proposal.status != "pending":
        raise AppError("conflict", "This suggestion was already decided.", status_code=409)
    return proposal


def _decide(proposal: Proposal, status: str) -> None:
    proposal.status = status
    proposal.decided_at = datetime.now(UTC)
    proposal.version += 1


async def approve(
    db: AsyncSession,
    user_id: uuid.UUID,
    proposal_id: uuid.UUID,
    edited_payload: dict[str, Any] | None = None,
) -> tuple[Proposal, Event | None]:
    """Applies a proposal (possibly edited by the owner) in one transaction (FR-138)."""
    proposal = await _pending(db, user_id, proposal_id)
    assert proposal.target_id is not None  # noqa: S101  (every kind so far has a target)
    if edited_payload is not None:
        proposal.payload = check_payload(CHANGES[proposal.kind], edited_payload)
    event = await apply_change(
        db,
        user_id,
        proposal.kind,
        proposal.target_id,
        proposal.payload,
        expected_version=proposal.base_version,
        actor=proposal.created_by,
        proposal_id=proposal.id,
        stale_code="stale_proposal",
    )
    _decide(proposal, "applied")
    await db.flush()
    await db.refresh(proposal)
    return proposal, event


async def reject(db: AsyncSession, user_id: uuid.UUID, proposal_id: uuid.UUID) -> Proposal:
    proposal = await _pending(db, user_id, proposal_id)
    _decide(proposal, "rejected")
    await db.flush()
    await db.refresh(proposal)
    return proposal
