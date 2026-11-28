import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record


class RefreshToken(Record, Base):
    """One refresh token. A sign-in creates a "family"; each refresh adds a token to it."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_id_family_id", "user_id", "family_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    family_id: Mapped[uuid.UUID]
    # Only the SHA-256 of the token is stored: a copy of the database cannot be used to sign in.
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(index=True)
    used_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip_hint: Mapped[str | None] = mapped_column(Text)
