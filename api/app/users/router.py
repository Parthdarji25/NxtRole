"""The signed-in owner: profile, password and signed-in devices."""

import uuid

from fastapi import APIRouter, Request

from app.auth import repository as sessions
from app.core.deps import CurrentUser
from app.history import service as history
from app.users import service
from app.users.schemas import (
    ChangePassword,
    ChangeProfile,
    Device,
    Devices,
    ProfileChanged,
    UserOut,
)

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/me", response_model=UserOut)
async def me(current: CurrentUser) -> UserOut:
    return UserOut.model_validate(current.user)


@router.patch("/account/profile", response_model=ProfileChanged)
async def change_profile(body: ChangeProfile, current: CurrentUser) -> ProfileChanged:
    event = await history.apply_change(
        current.db,
        current.user.id,
        "rename_profile",
        current.user.id,
        {"display_name": body.display_name},
        expected_version=body.version,
    )
    return ProfileChanged(
        user=UserOut.model_validate(current.user), event_id=event.id if event else None
    )


@router.post("/account/password", status_code=204)
async def change_password(body: ChangePassword, request: Request, current: CurrentUser) -> None:
    await service.change_password(
        current, request.app.state.redis, body.current_password, body.new_password
    )


@router.get("/account/sessions", response_model=Devices)
async def devices(current: CurrentUser) -> Devices:
    found = await sessions.active_sessions(current.db, current.user.id)
    return Devices(
        items=[
            Device(
                family_id=entry.family_id,
                signed_in_at=entry.signed_in_at,
                last_used_at=entry.last_used_at,
                user_agent=entry.user_agent,
                ip_hint=entry.ip_hint,
                current=entry.family_id == current.session_id,
            )
            for entry in found
        ]
    )


@router.delete("/account/sessions/{family_id}", status_code=204)
async def sign_out_device(family_id: uuid.UUID, current: CurrentUser) -> None:
    await service.sign_out_device(current, family_id)


@router.delete("/account/sessions", status_code=204)
async def sign_out_other_devices(current: CurrentUser) -> None:
    await service.sign_out_other_devices(current)
