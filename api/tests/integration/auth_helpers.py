"""Shared steps for the sign-in tests."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select

from app.ai.transport import Transport
from app.auth import passwords
from app.auth.models import RefreshToken
from app.config import Settings
from app.main import create_app
from app.users.models import User
from tests.conftest import running_client
from tests.integration.factories import owner_session

EMAIL = "owner@example.com"
PASSWORD = "a long quiet evening in pune"
NEW_PASSWORD = "the second long password here"
COOKIE = "__Secure-nr_refresh"
CSRF = {"X-NxtRole-CSRF": "1"}


@dataclass(frozen=True)
class Account:
    user: User
    recovery_code: str


async def make_user(settings: Settings, email: str = EMAIL) -> Account:
    code = passwords.new_recovery_code()
    user = User(
        email=email,
        password_hash=await passwords.hash_password(PASSWORD),
        recovery_code_hash=await passwords.hash_recovery_code(code),
    )
    async with owner_session(settings) as session:
        session.add(user)
    return Account(user, code)


async def reload_user(settings: Settings, email: str = EMAIL) -> User:
    async with owner_session(settings) as session:
        return (await session.scalars(select(User).where(User.email == email))).one()


async def stored_tokens(settings: Settings) -> list[RefreshToken]:
    async with owner_session(settings) as session:
        statement = select(RefreshToken).order_by(RefreshToken.created_at)
        return list((await session.scalars(statement)).all())


@asynccontextmanager
async def api(
    settings: Settings, *, transport: Transport | None = None, **changes: Any
) -> AsyncIterator[httpx.AsyncClient]:
    """The app as a browser sees it. One trusted forwarder, so a test can pick its address
    with `from_address`; a high sign-in rate unless the test is about the rate limit."""
    values: dict[str, Any] = {"trusted_proxy_count": 1, "login_rate_per_minute": 1000}
    app = create_app(settings.model_copy(update=values | changes), ai_transport=transport)
    # Secure cookies are only sent to secure addresses.
    async with running_client(app, base_url="https://test") as client:
        yield client


def from_address(ip: str) -> dict[str, str]:
    return {"X-Forwarded-For": ip}


async def sign_in(
    client: httpx.AsyncClient,
    email: str = EMAIL,
    password: str = PASSWORD,
    ip: str = "198.51.100.1",
) -> httpx.Response:
    return await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers=from_address(ip),
    )


@dataclass(frozen=True)
class Device:
    """One signed-in browser: its access token and its refresh cookie."""

    access_token: str
    refresh_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


async def device(client: httpx.AsyncClient, email: str = EMAIL) -> Device:
    response = await sign_in(client, email)
    assert response.status_code == 200, response.text
    token = response.cookies[COOKIE]
    client.cookies.clear()
    return Device(response.json()["access_token"], token)


async def refresh(client: httpx.AsyncClient, token: str) -> httpx.Response:
    """Refresh with exactly this cookie, whatever the client remembers."""
    client.cookies.clear()
    response = await client.post(
        "/api/auth/refresh", headers=CSRF | {"Cookie": f"{COOKIE}={token}"}
    )
    client.cookies.clear()
    return response


def code_of(response: httpx.Response) -> str:
    return str(response.json()["detail"]["code"])
