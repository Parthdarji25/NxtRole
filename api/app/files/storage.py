"""Private file storage. Files are found by id, never by a public address or a typed name.

Locally the files sit in a folder that git ignores. Production uses private cloud storage
behind the same interface (Phase 15).
"""

import asyncio
import uuid
from pathlib import Path
from typing import Protocol


def storage_path(user_id: uuid.UUID, file_id: uuid.UUID) -> str:
    # Only ids: nothing a person typed becomes part of a path.
    return f"{user_id}/{file_id}"


class Storage(Protocol):
    async def create(self, path: str, data: bytes) -> bool:
        """Stores new content. False if something is already there."""
        ...

    async def read(self, path: str) -> bytes | None: ...

    async def delete(self, path: str) -> None: ...


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _full(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if not full.is_relative_to(self.root) or full == self.root:
            raise ValueError("the path leaves the storage folder")
        return full

    async def create(self, path: str, data: bytes) -> bool:
        full = self._full(path)

        def write() -> bool:
            full.parent.mkdir(parents=True, exist_ok=True)
            try:
                # "x": fails if the file exists, so an upload address works once.
                with full.open("xb") as target:
                    target.write(data)
            except FileExistsError:
                return False
            return True

        return await asyncio.to_thread(write)

    async def read(self, path: str) -> bytes | None:
        full = self._full(path)

        def read() -> bytes | None:
            return full.read_bytes() if full.is_file() else None

        return await asyncio.to_thread(read)

    async def delete(self, path: str) -> None:
        await asyncio.to_thread(self._full(path).unlink, missing_ok=True)
