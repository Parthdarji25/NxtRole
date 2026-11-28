"""How the approve-and-undo engine reads and writes the career profile."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.history.snapshot import Snapshot, not_found
from app.profile import repository
from app.users import repository as users


class CareerProfileTarget:
    """The target id is the user's own id: each person has one profile."""

    async def read(self, db: AsyncSession, user_id: uuid.UUID, target_id: uuid.UUID) -> Snapshot:
        # Locking the user serialises changes, even before any version exists.
        if target_id != user_id or await users.get(db, user_id, lock=True) is None:
            raise not_found()
        current = await repository.approved(db, user_id)
        source = current.source_file_id if current else None
        values = {
            "facts": current.facts if current else None,
            "source_file_id": str(source) if source else None,
        }
        return Snapshot(values, await repository.latest_number(db, user_id))

    async def write(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        values: dict[str, Any],
    ) -> None:
        if target_id != user_id:
            raise not_found()
        source = values.get("source_file_id")
        await repository.add(db, user_id, values["facts"], uuid.UUID(source) if source else None)
