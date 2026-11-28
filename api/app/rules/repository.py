"""Database queries about rules. Every query is limited to one user."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rules.models import Rule

# The rules the owner sets from their preferences.
MIN_FIXED_PAY = "min_fixed_pay"
WORK_MODES = "work_modes"
EXCLUDE_COMPANY_TYPE = "exclude_company_type"


async def all_rules(db: AsyncSession, user_id: uuid.UUID) -> Sequence[Rule]:
    statement = select(Rule).where(Rule.user_id == user_id).order_by(Rule.kind, Rule.id)
    return (await db.scalars(statement)).all()


async def yours(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Rule]:
    statement = select(Rule).where(Rule.user_id == user_id, Rule.origin == "you")
    return {rule.kind: rule for rule in (await db.scalars(statement)).all()}


async def set_yours(
    db: AsyncSession, user_id: uuid.UUID, kind: str, value: dict[str, Any] | None
) -> None:
    """Creates, changes or removes (value None) the owner's rule of this kind."""
    existing = (await yours(db, user_id)).get(kind)
    if value is None:
        if existing is not None:
            await db.execute(delete(Rule).where(Rule.user_id == user_id, Rule.id == existing.id))
    elif existing is None:
        db.add(Rule(user_id=user_id, kind=kind, value=value, origin="you"))
    elif existing.value != value:
        existing.value = value
        existing.version += 1
    await db.flush()
