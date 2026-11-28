"""Walks every address the API offers. A new route that forgets to require sign-in fails
here (T-AUTH-7, E-70)."""

import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import delete

from app.auth import tokens
from app.config import Settings
from app.main import create_app
from app.users.models import User
from tests.integration.auth_helpers import api, code_of, device, make_user
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")

# The only addresses that work without an access token, and why.
OPEN = {
    ("get", "/health"),
    ("get", "/api/health"),
    ("get", "/api/health/ready"),
    ("post", "/api/auth/login"),
    ("post", "/api/auth/recover"),
    # These two need the refresh cookie and the CSRF header instead.
    ("post", "/api/auth/refresh"),
    ("post", "/api/auth/logout"),
    # This one needs the short-lived pass for that one file instead (D-029).
    ("put", "/api/files/{file_id}/content"),
}


def all_routes(settings: Settings) -> list[tuple[str, str]]:
    paths = create_app(settings).openapi()["paths"]
    return sorted((method, path) for path, methods in paths.items() for method in methods)


async def call(
    client: httpx.AsyncClient, method: str, path: str, headers: dict[str, str]
) -> httpx.Response:
    address = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
    return await client.request(method.upper(), address, headers=headers)


async def test_there_is_no_way_to_sign_up(test_settings: Settings) -> None:
    paths = " ".join(path for _, path in all_routes(test_settings))

    assert not re.search(r"register|sign-?up|create-(user|account|owner)", paths)
    assert ("post", "/api/proposals") not in all_routes(test_settings)


@pytest.mark.parametrize("token", ["none", "nonsense", "expired", "forged"])
async def test_every_route_refuses_a_visitor_without_a_valid_token(
    token: str, test_settings: Settings
) -> None:
    identity = tokens.Identity(uuid.uuid4(), uuid.uuid4())
    secret = test_settings.require_jwt_secret()
    headers = {
        "none": {},
        "nonsense": {"Authorization": "Bearer nonsense"},
        "expired": {
            "Authorization": "Bearer "
            + tokens.create_access_token(identity, secret, datetime.now(UTC) - timedelta(hours=1))
        },
        "forged": {"Authorization": "Bearer " + tokens.create_access_token(identity, secret[::-1])},
    }[token]
    expected = "token_expired" if token == "expired" else "unauthorized"
    protected = [route for route in all_routes(test_settings) if route not in OPEN]

    async with api(test_settings) as client:
        answers = {route: await call(client, *route, headers) for route in protected}

    assert len(protected) >= 10
    wrong = {
        route: (answer.status_code, answer.text)
        for route, answer in answers.items()
        if answer.status_code != 401 or code_of(answer) != expected
    }
    assert wrong == {}


@pytest.mark.parametrize("path", ["/api/auth/refresh", "/api/auth/logout"])
async def test_the_cookie_routes_refuse_a_request_without_the_header(
    path: str, test_settings: Settings
) -> None:
    async with api(test_settings) as client:
        response = await client.post(path)

    assert (response.status_code, code_of(response)) == (403, "csrf_missing")


async def test_the_upload_address_refuses_a_request_without_its_pass(
    test_settings: Settings,
) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        path = f"/api/files/{uuid.uuid4()}/content"
        no_pass = await client.put(path, content=b"x", headers=mine.headers)
        sign_in_only = await client.put(f"{path}?token={mine.access_token}", content=b"x")

    assert no_pass.status_code == 422
    assert (sign_in_only.status_code, code_of(sign_in_only)) == (403, "upload_expired")


async def test_a_deleted_account_is_refused_at_once(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        async with owner_session(test_settings) as session:
            await session.execute(delete(User))
        response = await client.get("/api/me", headers=mine.headers)

    assert response.status_code == 401
