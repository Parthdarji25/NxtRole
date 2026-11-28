"""What can be changed through history, and how each kind of record is read and written.

A feature that wants approval and undo adds two things here: a "target" (how to read and
write its records) and a "change" (what a proposal of that kind may set). Everything else,
such as versions, history rows and undo, is shared.
"""

import uuid
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.users import repository as users
from app.users.schemas import DisplayName


def not_found() -> AppError:
    # The same answer for "does not exist" and "belongs to someone else".
    return AppError("not_found", "That item does not exist.", status_code=404)


@dataclass(frozen=True)
class Snapshot:
    values: dict[str, Any]
    version: int


class Target(Protocol):
    async def read(self, db: AsyncSession, user_id: uuid.UUID, target_id: uuid.UUID) -> Snapshot:
        """The record now, locked until the transaction ends. Raises `not_found`."""
        ...

    async def write(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        values: dict[str, Any],
    ) -> None:
        """Sets these fields and moves the version on."""
        ...


class ProfileTarget:
    """The owner's profile. The only record that can be changed in Phase 4 (D-050)."""

    fields: Collection[str] = ("display_name",)

    async def read(self, db: AsyncSession, user_id: uuid.UUID, target_id: uuid.UUID) -> Snapshot:
        user = await users.get(db, user_id, lock=True) if target_id == user_id else None
        if user is None:
            raise not_found()
        return Snapshot({name: getattr(user, name) for name in self.fields}, user.version)

    async def write(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        values: dict[str, Any],
    ) -> None:
        user = await users.get(db, user_id, lock=True) if target_id == user_id else None
        if user is None:
            raise not_found()
        for name in self.fields:
            if name in values:
                setattr(user, name, values[name])
        user.version += 1
        await db.flush()


class RenameProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: DisplayName | None


@dataclass(frozen=True)
class Change:
    target_type: str
    # The name written into history.
    action: str
    # Every proposal and request of this kind is checked against this shape.
    payload: type[BaseModel]


TARGETS: dict[str, Target] = {"profile": ProfileTarget()}

CHANGES: dict[str, Change] = {
    "rename_profile": Change("profile", "profile.name_changed", RenameProfile),
}
