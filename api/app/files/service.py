"""Accepting an upload: a pass to send it, then checking what arrived (FR-013, FR-023)."""

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.privacy import Detected, detect
from app.core.errors import AppError
from app.files import text
from app.files.models import File
from app.files.storage import Storage, storage_path

RESUME = "resume"
UNFINISHED_KEPT = timedelta(days=1)
MAX_NAME_LENGTH = 120


def not_found() -> AppError:
    return AppError("not_found", "That file does not exist.", status_code=404)


def display_name(typed: str) -> str:
    """A file name safe to show: no folders, no control characters, not too long."""
    name = re.split(r"[\\/]", typed)[-1]
    name = "".join(character for character in name if character.isprintable()).strip()
    return name[-MAX_NAME_LENGTH:] or "resume"


@dataclass(frozen=True)
class Checked:
    file: File
    detected: Detected
    warnings: list[str]
    # True when the same file had been uploaded before.
    duplicate: bool = False


async def get(db: AsyncSession, user_id: uuid.UUID, file_id: uuid.UUID) -> File:
    statement = (
        select(File)
        .where(File.user_id == user_id, File.id == file_id, File.status != "deleted")
        .with_for_update()
    )
    found = (await db.scalars(statement)).one_or_none()
    if found is None:
        raise not_found()
    return found


async def create(
    db: AsyncSession,
    storage: Storage,
    user_id: uuid.UUID,
    content_type: str,
    size: int,
    name: str,
) -> File:
    if content_type not in text.KINDS:
        raise text.wrong_kind()
    if size > text.MAX_BYTES:
        raise text.refused("file_too_large", "That file is over 5 MB.", 413)
    await _remove_unfinished(db, storage, user_id)
    file_id = uuid.uuid4()
    record = File(
        id=file_id,
        user_id=user_id,
        kind=RESUME,
        storage_path=storage_path(user_id, file_id),
        original_name=display_name(name),
        content_type=content_type,
        size_bytes=size,
        expires_at=datetime.now(UTC) + UNFINISHED_KEPT,
    )
    db.add(record)
    await db.flush()
    return record


async def _remove_unfinished(db: AsyncSession, storage: Storage, user_id: uuid.UUID) -> None:
    """Housekeeping: uploads started long ago and never finished."""
    expired = delete(File).where(
        File.user_id == user_id, File.status == "pending", File.expires_at < datetime.now(UTC)
    )
    for path in (await db.scalars(expired.returning(File.storage_path))).all():
        await storage.delete(path)


async def check(
    db: AsyncSession, storage: Storage, user_id: uuid.UUID, file_id: uuid.UUID
) -> Checked | AppError:
    """Reads the uploaded bytes. A refusal is returned, not raised, so that the rejection
    is saved; the refused bytes are deleted."""
    record = await get(db, user_id, file_id)
    if record.status == "ready":
        assert record.text_content is not None  # noqa: S101
        return Checked(record, detect(record.text_content), [])
    data = await storage.read(record.storage_path)
    if record.status != "pending" or data is None:
        raise AppError("file_not_ready", "Upload the file first.", status_code=409)
    try:
        extracted = await text.read_resume(data, record.content_type)
    except AppError as error:
        await storage.delete(record.storage_path)
        record.status = "rejected"
        return error

    digest = hashlib.sha256(data).hexdigest()
    earlier = (
        await db.scalars(
            select(File)
            .where(
                File.user_id == user_id,
                File.status == "ready",
                File.sha256 == digest,
                File.id != record.id,
            )
            .limit(1)
        )
    ).first()
    if earlier is not None:
        assert earlier.text_content is not None  # noqa: S101
        await storage.delete(record.storage_path)
        await db.delete(record)
        return Checked(earlier, detect(earlier.text_content), [], duplicate=True)

    record.status = "ready"
    record.size_bytes = len(data)
    record.sha256 = digest
    record.text_content = extracted.text
    record.truncated = extracted.truncated
    record.expires_at = None
    await db.flush()
    return Checked(record, detect(extracted.text), extracted.warnings)


async def remove(
    db: AsyncSession, storage: Storage, user_id: uuid.UUID, file_id: uuid.UUID
) -> None:
    record = await get(db, user_id, file_id)
    await storage.delete(record.storage_path)
    record.status = "deleted"
    record.sha256 = None
    record.text_content = None
    record.hidden_identity = None
