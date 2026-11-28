"""Stops two tabs from silently overwriting each other ("optimistic concurrency", E-27).

Every editable record has a version number. A change says which version it was based on;
if the record moved on in the meantime, the change is refused.
"""

from app.core.errors import AppError


def ensure_version(current: int, expected: int) -> None:
    if current != expected:
        raise AppError(
            "conflict",
            "This was changed somewhere else. Reload to see the latest, then try again.",
            status_code=409,
            extra={"current_version": current},
        )
