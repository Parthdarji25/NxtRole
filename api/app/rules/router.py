"""The owner's rules under /api/rules. Adding and editing them here arrives in Phase 7."""

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.deps import CurrentUser
from app.preferences.values import lakhs
from app.rules import repository

router = APIRouter(prefix="/api/rules", tags=["rules"])

WORK_MODE_WORDS = {"remote": "remote", "hybrid": "hybrid", "onsite": "on-site"}


class RuleOut(BaseModel):
    id: uuid.UUID
    kind: str
    # The rule in words.
    text: str
    # "you" (set by the owner) or "learned" (from Phase 7).
    origin: str
    status: str
    # How many jobs it has hidden (from Phase 7).
    hid_count: int


class Rules(BaseModel):
    items: list[RuleOut]


def describe(kind: str, value: dict[str, Any]) -> str:
    if kind == repository.MIN_FIXED_PAY:
        return f"Fixed pay of ₹{lakhs(value['amount_inr'])} lakh a year or more"
    if kind == repository.WORK_MODES:
        wanted = [WORK_MODE_WORDS[mode] for mode in value["modes"]]
        return f"Only {' or '.join(wanted)} jobs"
    if kind == repository.EXCLUDE_COMPANY_TYPE:
        return f"Skip these kinds of company: {', '.join(value['types'])}"
    return kind.replace("_", " ").capitalize()


@router.get("", response_model=Rules)
async def list_rules(current: CurrentUser) -> Rules:
    found = await repository.all_rules(current.db, current.user.id)
    return Rules(
        items=[
            RuleOut(
                id=rule.id,
                kind=rule.kind,
                text=describe(rule.kind, rule.value),
                origin=rule.origin,
                status=rule.status,
                hid_count=rule.hid_count,
            )
            for rule in found
        ]
    )
