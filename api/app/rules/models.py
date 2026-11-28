import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record


class Rule(Record, Base):
    __tablename__ = "rules"
    __table_args__ = (
        CheckConstraint("origin IN ('you', 'learned')", name="origin"),
        CheckConstraint("status IN ('active', 'suggested', 'dismissed')", name="status"),
        Index("ix_rules_user_id_status", "user_id", "status"),
        # The owner has one rule of each kind.
        Index(
            "uq_rules_user_id_kind_you",
            "user_id",
            "kind",
            unique=True,
            postgresql_where=text("origin = 'you'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    origin: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="active")
    # For learned suggestions (Phase 7).
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dismissed_until: Mapped[datetime | None]
    hid_count: Mapped[int] = mapped_column(server_default=text("0"))
    version: Mapped[int] = mapped_column(server_default=text("1"))
