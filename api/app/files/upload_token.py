"""The short-lived, single-file pass in an upload address (D-029, T-FILE-2)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.errors import AppError

LIFETIME = timedelta(minutes=10)
ALGORITHM = "HS256"


@dataclass(frozen=True)
class UploadPass:
    user_id: uuid.UUID
    file_id: uuid.UUID


def create(user_id: uuid.UUID, file_id: uuid.UUID, secret: str) -> tuple[str, datetime]:
    expires = datetime.now(UTC) + LIFETIME
    claims = {
        "sub": str(user_id),
        "fid": str(file_id),
        # Different from "access", so one can never be used as the other.
        "type": "upload",
        "exp": expires,
    }
    return jwt.encode(claims, secret, algorithm=ALGORITHM), expires


def read(token: str, file_id: uuid.UUID, secret: str) -> UploadPass:
    refused = AppError(
        "upload_expired",
        "That upload address is no longer valid. Choose the file again.",
        status_code=403,
    )
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "fid", "type", "exp"]},
        )
        if claims["type"] != "upload" or uuid.UUID(claims["fid"]) != file_id:
            raise refused
        return UploadPass(uuid.UUID(claims["sub"]), file_id)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise refused from None
