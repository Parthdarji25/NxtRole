"""Makes a repeated "create" request safe (FR-218, E-34).

The browser sends an `Idempotency-Key`. The first request does the work and stores the answer;
a repeat with the same key and body gets the stored answer, and nothing is created twice.
"""

import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Header
from sqlalchemy import ForeignKey, Text, UniqueConstraint, delete, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.errors import AppError
from app.db.base import Base, Record

KEEP_FOR = timedelta(hours=24)

IdempotencyKeyHeader = Annotated[
    str | None, Header(alias="Idempotency-Key", min_length=8, max_length=200)
]


class IdempotencyKey(Record, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idempotency_keys_user_id_key"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(Text)
    request_hash: Mapped[str] = mapped_column(Text)
    status_code: Mapped[int]
    response: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expires_at: Mapped[datetime]


@dataclass(frozen=True)
class Answer:
    status_code: int
    body: dict[str, Any]
    replayed: bool = False


def fingerprint(request_body: dict[str, Any]) -> str:
    canonical = json.dumps(request_body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def run_once(
    session: AsyncSession,
    user_id: uuid.UUID,
    key: str,
    request_body: dict[str, Any],
    action: Callable[[], Awaitable[tuple[int, dict[str, Any]]]],
) -> Answer:
    """Runs `action` at most once per key. Everything happens in the caller's transaction, so
    if the action fails, the key is not kept and the request can be tried again."""
    request_hash = fingerprint(request_body)
    now = datetime.now(UTC)
    mine = (IdempotencyKey.user_id == user_id, IdempotencyKey.key == key)
    await session.execute(delete(IdempotencyKey).where(*mine, IdempotencyKey.expires_at <= now))
    # Claiming the key first means a second request waits here until the first one finishes.
    claimed = await session.scalar(
        insert(IdempotencyKey)
        .values(
            user_id=user_id,
            key=key,
            request_hash=request_hash,
            status_code=0,
            response={},
            expires_at=now + KEEP_FOR,
        )
        .on_conflict_do_nothing(index_elements=["user_id", "key"])
        .returning(IdempotencyKey.id)
    )
    if claimed is None:
        stored = (await session.scalars(select(IdempotencyKey).where(*mine))).one()
        if stored.request_hash != request_hash:
            raise AppError(
                "idempotency_conflict",
                "This request key was already used for something else. Reload and try again.",
                status_code=409,
            )
        return Answer(stored.status_code, stored.response, replayed=True)

    status_code, body = await action()
    row = (await session.scalars(select(IdempotencyKey).where(*mine))).one()
    row.status_code = status_code
    row.response = body
    return Answer(status_code, body)
