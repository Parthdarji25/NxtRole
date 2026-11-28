import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record

FILE_STATUSES = ("pending", "ready", "rejected", "deleted")


class File(Record, Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{status}'" for status in FILE_STATUSES) + ")",
            name="status",
        ),
        Index("ix_files_user_id_kind", "user_id", "kind"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    # Where the bytes are, relative to private storage. Built from ids only.
    storage_path: Mapped[str] = mapped_column(Text)
    # Shown on screen. Never used to build a path.
    original_name: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="pending")
    # The text read from the file (personal data), and what the owner confirmed to hide.
    text_content: Mapped[str | None] = mapped_column(Text)
    truncated: Mapped[bool] = mapped_column(server_default="false")
    hidden_identity: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # An upload that never finishes is removed after this.
    expires_at: Mapped[datetime | None]
