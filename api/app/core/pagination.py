"""Long lists are sent one page at a time, using a "cursor": a bookmark for where the last
page ended. Unlike page numbers, it does not skip or repeat rows when new ones arrive."""

import base64
import binascii
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.errors import AppError

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]
Cursor = Annotated[str | None, Query(max_length=200)]


class Page[Item](BaseModel):
    items: list[Item]
    next_cursor: str | None


def encode_cursor(when: datetime, row_id: UUID) -> str:
    return base64.urlsafe_b64encode(f"{when.isoformat()}|{row_id}".encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        when, row_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        parsed = datetime.fromisoformat(when)
        if parsed.tzinfo is None:
            raise ValueError("a time zone is required")
        return parsed, UUID(row_id)
    except (ValueError, binascii.Error):
        raise AppError(
            "validation_error", "That page link is not valid. Reload the list.", status_code=422
        ) from None


async def newest_first[Row](
    session: AsyncSession,
    statement: Select[Row],
    time_column: InstrumentedAttribute[datetime],
    id_column: InstrumentedAttribute[Any],
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Row], str | None]:
    """Rows newest first, plus the cursor for the next page (None on the last page)."""
    if cursor is not None:
        when, row_id = decode_cursor(cursor)
        statement = statement.where(tuple_(time_column, id_column) < tuple_(when, row_id))
    ordered = statement.order_by(time_column.desc(), id_column.desc()).limit(limit + 1)
    rows = (await session.scalars(ordered)).all()
    if len(rows) <= limit:
        return rows, None
    last = rows[limit - 1]
    return rows[:limit], encode_cursor(getattr(last, time_column.key), getattr(last, id_column.key))
