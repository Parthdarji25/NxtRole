"""What every kind of record that supports approval and undo hands to the engine."""

from dataclasses import dataclass
from typing import Any

from app.core.errors import AppError


def not_found() -> AppError:
    # The same answer for "does not exist" and "belongs to someone else".
    return AppError("not_found", "That item does not exist.", status_code=404)


@dataclass(frozen=True)
class Snapshot:
    values: dict[str, Any]
    version: int
