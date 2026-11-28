import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SearchPreferences(Base):
    __tablename__ = "search_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    titles: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    places: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    experience_min: Mapped[int | None] = mapped_column(SmallInteger)
    experience_max: Mapped[int | None] = mapped_column(SmallInteger)
    notice_days: Mapped[int | None] = mapped_column(SmallInteger)
    expected_ctc_inr: Mapped[int | None] = mapped_column(BigInteger)
    # Where the owner stopped in setup (FR-020).
    onboarding_step: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))
    version: Mapped[int] = mapped_column(server_default=text("1"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
