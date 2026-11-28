from datetime import datetime

from sqlalchemy import CheckConstraint, Text, func, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Record

MAX_NAME_LENGTH = 80


class User(Record, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"char_length(display_name) BETWEEN 1 AND {MAX_NAME_LENGTH}",
            name="display_name_length",
        ),
    )

    # CITEXT compares without regard to capitals, so one address cannot be used twice.
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    recovery_code_hash: Mapped[str] = mapped_column(Text)
    # Shown on screens only. Never sent to an AI provider.
    display_name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    failed_logins: Mapped[int] = mapped_column(server_default=text("0"))
    last_failed_at: Mapped[datetime | None]
    locked_until: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(server_default=text("1"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
