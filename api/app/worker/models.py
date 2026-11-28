import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record

JOB_STATES = ("queued", "running", "done", "failed", "dead")


class BackgroundJob(Record, Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        CheckConstraint(
            "state IN (" + ", ".join(f"'{state}'" for state in JOB_STATES) + ")", name="state"
        ),
        Index("ix_background_jobs_state_run_after", "state", "run_after"),
        # A double tap makes one job (E-45).
        Index(
            "uq_background_jobs_active_dedupe_key",
            "dedupe_key",
            unique=True,
            postgresql_where=text("state IN ('queued', 'running')"),
        ),
    )

    # Empty for system work.
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    # Ids only, never personal text.
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    # Ids and counts only.
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(Text, server_default="queued")
    run_after: Mapped[datetime] = mapped_column(server_default=func.now())
    attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    max_attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("5"))
    locked_by: Mapped[str | None] = mapped_column(Text)
    locked_at: Mapped[datetime | None]
    dedupe_key: Mapped[str | None] = mapped_column(Text)
    # An error code, never a message with data in it.
    last_error: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[datetime | None]
