import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record

PROPOSAL_STATUSES = ("pending", "approved", "rejected", "expired", "applied", "failed")


class Proposal(Record, Base):
    """A change that waits for the owner: the only way AI changes data."""

    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{status}'" for status in PROPOSAL_STATUSES) + ")",
            name="status",
        ),
        Index("ix_proposals_user_id_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(server_default=text("1"))
    kind: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str] = mapped_column(Text)
    target_id: Mapped[uuid.UUID | None]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # The version of the target when this was proposed. If it moved on, the proposal is stale.
    base_version: Mapped[int | None]
    status: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
    created_by: Mapped[str] = mapped_column(Text)
    # The agent run that made it (the table arrives in Phase 10).
    run_id: Mapped[uuid.UUID | None]
    decided_at: Mapped[datetime | None]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Event(Base):
    """One entry of history. Rows are only added; undoing adds another row."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_user_id_occurred_at", "user_id", text("occurred_at DESC")),
        Index("ix_events_target_type_target_id", "target_type", "target_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now())
    actor: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str] = mapped_column(Text)
    target_id: Mapped[uuid.UUID]
    # The changed fields only, as they were and as they became.
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    proposal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("proposals.id"))
    undone_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id"))
    undo_of: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id"))
    note: Mapped[str | None] = mapped_column(Text)
