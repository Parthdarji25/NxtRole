"""Settings about AI: what it may see, which models are used, and how much (FR-197 to 199)."""

from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.ai.budget import Budget
from app.ai.models import Role, chain
from app.ai.usage import PROVIDER, Status, ai_status, recent_usage
from app.core.deps import CurrentUser

router = APIRouter(prefix="/api/settings", tags=["ai"])


class Model(BaseModel):
    role: str
    name: str


class Day(BaseModel):
    day: date
    model: str
    requests: int
    tokens_in: int
    tokens_out: int
    errors: int
    rate_limited: int


class Ai(BaseModel):
    status: Status
    provider: str
    models: list[Model]
    requests_per_day: int
    tokens_per_day: int
    # The last seven days.
    usage: list[Day]


class Privacy(BaseModel):
    # Always true: it is not a switch (FR-199).
    identity_hidden: bool = True
    # The day the owner said Zero Data Retention is on. null: not confirmed.
    zero_data_retention_confirmed_on: date | None
    status: Status


@router.get("/ai", response_model=Ai)
async def ai(request: Request, current: CurrentUser) -> Ai:
    settings = request.app.state.settings
    budget = Budget(request.app.state.redis, settings)
    rows = await recent_usage(current.db, current.user.id)
    return Ai(
        status=await ai_status(budget, settings),
        provider=PROVIDER,
        models=[Model(role=role.value, name=chain(settings, role)[0]) for role in Role],
        requests_per_day=settings.ai_requests_per_day,
        tokens_per_day=settings.ai_tokens_per_day,
        usage=[Day.model_validate(row, from_attributes=True) for row in rows],
    )


@router.get("/privacy", response_model=Privacy)
async def privacy(request: Request, current: CurrentUser) -> Privacy:
    settings = request.app.state.settings
    budget = Budget(request.app.state.redis, settings)
    return Privacy(
        zero_data_retention_confirmed_on=settings.groq_zdr_confirmed_on,
        status=await ai_status(budget, settings),
    )
