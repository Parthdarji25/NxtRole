"""Uploading under /api/files. The bytes go to a short-lived address, then are checked."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.ai.privacy import Detected, Identity
from app.core.deps import CurrentUser
from app.core.errors import AppError, error_response
from app.db.session import set_current_user
from app.files import service, text, upload_token
from app.files.models import File
from app.files.storage import Storage

router = APIRouter(prefix="/api/files", tags=["files"])


class NewUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=300)
    content_type: str = Field(max_length=200)
    size: int = Field(ge=1)


class Upload(BaseModel):
    file_id: uuid.UUID
    # Send the bytes here with PUT.
    upload_url: str
    expires_at: str


class FileOut(BaseModel):
    id: uuid.UUID
    name: str
    content_type: str
    size_bytes: int
    status: str
    truncated: bool
    # What the owner confirmed to hide, if this file has been read by AI before.
    hidden_identity: Identity | None

    @classmethod
    def of(cls, record: File) -> "FileOut":
        return cls(
            id=record.id,
            name=record.original_name,
            content_type=record.content_type,
            size_bytes=record.size_bytes,
            status=record.status,
            truncated=record.truncated,
            hidden_identity=record.hidden_identity,
        )


class CheckedFile(BaseModel):
    file: FileOut
    # What code found that should probably be hidden from AI.
    detected: Detected
    warnings: list[str]
    duplicate: bool


def storage_of(request: Request) -> Storage:
    storage: Storage = request.app.state.storage
    return storage


@router.post("/uploads", response_model=Upload, status_code=201)
async def start_upload(body: NewUpload, request: Request, current: CurrentUser) -> Upload:
    record = await service.create(
        current.db,
        storage_of(request),
        current.user.id,
        body.content_type,
        body.size,
        body.filename,
    )
    secret = request.app.state.settings.require_jwt_secret()
    token, expires = upload_token.create(current.user.id, record.id, secret)
    return Upload(
        file_id=record.id,
        upload_url=f"/api/files/{record.id}/content?token={token}",
        expires_at=expires.isoformat(),
    )


@router.put("/{file_id}/content", status_code=204)
async def receive(
    file_id: uuid.UUID,
    request: Request,
    token: Annotated[str, Query(max_length=1_000)],
) -> Response:
    """The upload address: the pass in it is the permission, so no sign-in header is sent."""
    secret = request.app.state.settings.require_jwt_secret()
    allowed = upload_token.read(token, file_id, secret)
    data = await request.body()
    async with request.app.state.sessions.begin() as db:
        await set_current_user(db, allowed.user_id)
        record = await service.get(db, allowed.user_id, file_id)
        if len(data) > text.MAX_BYTES:
            raise text.refused("file_too_large", "That file is over 5 MB.", 413)
        if record.status != "pending" or not await storage_of(request).create(
            record.storage_path, data
        ):
            raise AppError(
                "already_uploaded",
                "That file was already uploaded. Choose it again to replace it.",
                status_code=409,
            )
    return Response(status_code=204)


@router.post("/{file_id}/complete", response_model=CheckedFile)
async def complete(
    file_id: uuid.UUID, request: Request, current: CurrentUser
) -> CheckedFile | JSONResponse:
    result = await service.check(current.db, storage_of(request), current.user.id, file_id)
    if isinstance(result, AppError):
        # Returned, not raised: the rejection is saved with the transaction.
        return error_response(result.status_code, result.code, result.message)
    return CheckedFile(
        file=FileOut.of(result.file),
        detected=result.detected,
        warnings=result.warnings,
        duplicate=result.duplicate,
    )


@router.get("/{file_id}", response_model=FileOut)
async def read(file_id: uuid.UUID, current: CurrentUser) -> FileOut:
    return FileOut.of(await service.get(current.db, current.user.id, file_id))


@router.delete("/{file_id}", status_code=204)
async def remove(file_id: uuid.UUID, request: Request, current: CurrentUser) -> None:
    await service.remove(current.db, storage_of(request), current.user.id, file_id)
