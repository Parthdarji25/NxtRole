"""The shapes of account requests and answers."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.users.models import MAX_NAME_LENGTH

DisplayName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        # No control characters such as line breaks.
        pattern=r"^[^\x00-\x1f\x7f]+$",
    ),
]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    version: int


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChangePassword(Request):
    current_password: str = Field(min_length=1, max_length=1000)
    new_password: str = Field(min_length=1, max_length=1000)


class ChangeProfile(Request):
    # null removes the name.
    display_name: DisplayName | None
    # The version the change was based on (E-27).
    version: int = Field(ge=1)


class ProfileChanged(BaseModel):
    user: UserOut
    # Undo with POST /api/events/{event_id}/undo. null when nothing changed.
    event_id: uuid.UUID | None


class Device(BaseModel):
    family_id: uuid.UUID
    signed_in_at: datetime
    last_used_at: datetime
    user_agent: str | None
    ip_hint: str | None
    current: bool


class Devices(BaseModel):
    items: list[Device]
