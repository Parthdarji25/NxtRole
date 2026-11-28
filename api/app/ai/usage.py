"""How much AI was used, per day and model (FR-198), and whether it is working."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy import ForeignKey, Text, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.ai.budget import Budget
from app.ai.models import Role, chain
from app.config import Settings
from app.db.base import Base
from app.db.session import set_current_user

IST = ZoneInfo("Asia/Kolkata")
PROVIDER = "groq"
DAYS_SHOWN = 7

Status = Literal["normal", "using_backup", "limits_used", "not_set_up", "privacy_not_confirmed"]


class AiUsage(Base):
    __tablename__ = "ai_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # The day in India.
    day: Mapped[date] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(Text, primary_key=True)
    model: Mapped[str] = mapped_column(Text, primary_key=True)
    requests: Mapped[int] = mapped_column(server_default=text("0"))
    tokens_in: Mapped[int] = mapped_column(server_default=text("0"))
    tokens_out: Mapped[int] = mapped_column(server_default=text("0"))
    errors: Mapped[int] = mapped_column(server_default=text("0"))
    rate_limited: Mapped[int] = mapped_column(server_default=text("0"))


@dataclass(frozen=True)
class Used:
    requests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    errors: int = 0
    rate_limited: int = 0


class UsageLog:
    """Writes each call's counts in its own short transaction, so they are kept even when
    the work around the call fails."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID) -> None:
        self.sessions = sessions
        self.user_id = user_id

    async def __call__(self, model: str, used: Used) -> None:
        counts = {
            "requests": used.requests,
            "tokens_in": used.tokens_in,
            "tokens_out": used.tokens_out,
            "errors": used.errors,
            "rate_limited": used.rate_limited,
        }
        statement = insert(AiUsage).values(
            user_id=self.user_id,
            day=datetime.now(IST).date(),
            provider=PROVIDER,
            model=model,
            **counts,
        )
        statement = statement.on_conflict_do_update(
            index_elements=["user_id", "day", "provider", "model"],
            set_={name: getattr(AiUsage, name) + value for name, value in counts.items()},
        )
        async with self.sessions.begin() as db:
            await set_current_user(db, self.user_id)
            await db.execute(statement)


async def recent_usage(db: AsyncSession, user_id: uuid.UUID) -> Sequence[AiUsage]:
    since = datetime.now(IST).date() - timedelta(days=DAYS_SHOWN - 1)
    statement = (
        select(AiUsage)
        .where(AiUsage.user_id == user_id, AiUsage.day >= since)
        .order_by(AiUsage.day.desc(), AiUsage.model)
    )
    return (await db.scalars(statement)).all()


async def ai_status(budget: Budget, settings: Settings) -> Status:
    """One word for the banners: working, on the backup model, or waiting."""
    if settings.groq_api_key is None:
        return "not_set_up"
    if settings.groq_zdr_confirmed_on is None:
        return "privacy_not_confirmed"
    models = chain(settings, Role.MAIN)
    free = [not await budget.blocked_for(model) for model in models]
    if free[0]:
        return "normal"
    return "using_backup" if any(free) else "limits_used"
