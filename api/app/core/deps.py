"""What routes ask FastAPI to prepare for them: who is asking, and a database transaction."""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository, tokens
from app.auth.service import AuthService, Visitor
from app.core.client_ip import client_ip
from app.db.session import set_current_user
from app.users import repository as users
from app.users.models import User

bearer = HTTPBearer(auto_error=False)


def get_visitor(request: Request) -> Visitor:
    settings = request.app.state.settings
    return Visitor(
        ip=client_ip(request, settings.trusted_proxy_count),
        user_agent=request.headers.get("user-agent"),
    )


def get_auth_service(request: Request) -> AuthService:
    state = request.app.state
    return AuthService(state.sessions, state.redis, state.settings)


@dataclass(frozen=True)
class SignedInUser:
    """A transaction that can see only this user's rows."""

    db: AsyncSession
    user: User
    session_id: uuid.UUID


async def require_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AsyncIterator[SignedInUser]:
    """Refuses the request without a valid access token of a sign-in that is still alive.
    The transaction is saved when the route succeeds and undone when it fails."""
    if credentials is None:
        raise tokens.unauthorized()
    secret = request.app.state.settings.require_jwt_secret()
    identity = tokens.read_access_token(credentials.credentials, secret)
    async with request.app.state.sessions.begin() as db:
        await set_current_user(db, identity.user_id)
        user = await users.get(db, identity.user_id)
        # Checked on every request, so signing out a device takes effect at once.
        alive = await repository.is_signed_in(db, identity.user_id, identity.session_id)
        if user is None or not user.is_active or not alive:
            raise tokens.unauthorized()
        yield SignedInUser(db, user, identity.session_id)


# scope="function": the transaction is saved before the answer is sent, so "success" is true.
CurrentUser = Annotated[SignedInUser, Depends(require_user, scope="function")]
CurrentVisitor = Annotated[Visitor, Depends(get_visitor)]
Auth = Annotated[AuthService, Depends(get_auth_service)]
