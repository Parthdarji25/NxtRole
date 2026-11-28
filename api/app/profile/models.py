import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record


class ProfileVersion(Record, Base):
    """One approved set of facts. A change makes a new version; old ones are kept."""

    __tablename__ = "profile_versions"
    __table_args__ = (
        CheckConstraint("status IN ('approved', 'superseded')", name="status"),
        UniqueConstraint("user_id", "version_no", name="uq_profile_versions_user_id_version_no"),
        # At most one version is in use.
        Index(
            "uq_profile_versions_user_id_approved",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'approved'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    version_no: Mapped[int]
    status: Mapped[str] = mapped_column(Text)
    facts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    # The resume the facts came from.
    source_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None]
