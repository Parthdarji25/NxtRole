"""Staying signed in, signing out, and a stolen refresh token."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update

from app.auth.models import RefreshToken
from app.auth.tokens import hash_refresh_token
from app.config import Settings
from tests.integration.auth_helpers import (
    COOKIE,
    CSRF,
    api,
    code_of,
    device,
    make_user,
    refresh,
    stored_tokens,
)
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")


async def age(settings: Settings, token: str, **columns: datetime) -> None:
    """Pretends time has passed for one token."""
    async with owner_session(settings) as session:
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_refresh_token(token))
            .values(**columns)
        )


def seconds_ago(seconds: float) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=seconds)


async def test_refresh_without_the_header_is_forbidden(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        refused = await client.post(
            "/api/auth/refresh", headers={"Cookie": f"{COOKIE}={mine.refresh_token}"}
        )
        allowed = await refresh(client, mine.refresh_token)

    assert refused.status_code == 403
    assert code_of(refused) == "csrf_missing"
    assert "set-cookie" not in refused.headers
    assert allowed.status_code == 200


@pytest.mark.parametrize("cookie", [None, "never-issued-token"])
async def test_refresh_without_a_known_cookie_is_refused(
    cookie: str | None, test_settings: Settings
) -> None:
    async with api(test_settings) as client:
        headers = CSRF | ({"Cookie": f"{COOKIE}={cookie}"} if cookie else {})
        response = await client.post("/api/auth/refresh", headers=headers)

    assert response.status_code == 401
    assert code_of(response) == "invalid_refresh"
    # The useless cookie is removed.
    assert f'{COOKIE}=""' in response.headers["set-cookie"]


async def test_refresh_gives_new_tokens_in_the_same_sign_in(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        response = await refresh(client, mine.refresh_token)
        new_access = response.json()["access_token"]
        me = await client.get("/api/me", headers={"Authorization": f"Bearer {new_access}"})

    assert response.status_code == 200
    assert response.cookies[COOKIE] != mine.refresh_token
    assert new_access != mine.access_token
    assert me.status_code == 200
    old, new = await stored_tokens(test_settings)
    assert old.used_at is not None and new.used_at is None
    assert old.family_id == new.family_id


async def test_two_tabs_racing_both_continue(test_settings: Settings) -> None:
    """E-23: the same cookie used twice within 10 seconds."""
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        first = await refresh(client, mine.refresh_token)
        second = await refresh(client, mine.refresh_token)
        next_one = await refresh(client, first.cookies[COOKIE])

    assert first.status_code == second.status_code == next_one.status_code == 200
    # The second answer must not replace the cookie the browser already holds.
    assert "set-cookie" not in second.headers
    assert second.json()["access_token"]


async def test_simultaneous_refreshes_create_one_new_token(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        headers = CSRF | {"Cookie": f"{COOKIE}={mine.refresh_token}"}
        answers = await asyncio.gather(
            *(client.post("/api/auth/refresh", headers=headers) for _ in range(5))
        )

    assert [answer.status_code for answer in answers] == [200] * 5
    assert sum("set-cookie" in answer.headers for answer in answers) == 1
    assert len(await stored_tokens(test_settings)) == 2


async def test_auth_reused_refresh_token_revokes_family(test_settings: Settings) -> None:
    """E-24: a copy of an old token appears later."""
    await make_user(test_settings)

    async with api(test_settings) as client:
        victim = await device(client)
        other = await device(client)
        rotated = await refresh(client, victim.refresh_token)
        await age(test_settings, victim.refresh_token, used_at=seconds_ago(11))

        thief = await refresh(client, victim.refresh_token)
        owner = await refresh(client, rotated.cookies[COOKIE])
        old_access = await client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {rotated.json()['access_token']}"},
        )
        unaffected = await client.get("/api/me", headers=other.headers)

    assert thief.status_code == 401
    assert code_of(thief) == "session_reused"
    assert f'{COOKIE}=""' in thief.headers["set-cookie"]
    assert code_of(owner) == "session_reused"
    assert old_access.status_code == 401
    assert unaffected.status_code == 200


async def test_an_expired_refresh_token_is_refused(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        await age(test_settings, mine.refresh_token, expires_at=seconds_ago(1))
        response = await refresh(client, mine.refresh_token)
        me = await client.get("/api/me", headers=mine.headers)

    assert code_of(response) == "invalid_refresh"
    # An expired sign-in also ends the access token that came with it.
    assert me.status_code == 401


async def test_logout_ends_this_sign_in_only(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        other = await device(client)
        response = await client.post(
            "/api/auth/logout", headers=CSRF | {"Cookie": f"{COOKIE}={mine.refresh_token}"}
        )
        again = await refresh(client, mine.refresh_token)
        me = await client.get("/api/me", headers=mine.headers)
        still = await client.get("/api/me", headers=other.headers)

    assert response.status_code == 204
    assert f'{COOKIE}=""' in response.headers["set-cookie"]
    assert again.status_code == 401
    assert me.status_code == 401
    assert still.status_code == 200


async def test_logout_needs_the_header_and_a_cookie(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        mine = await device(client)
        no_header = await client.post(
            "/api/auth/logout", headers={"Cookie": f"{COOKIE}={mine.refresh_token}"}
        )
        no_cookie = await client.post("/api/auth/logout", headers=CSRF)
        me = await client.get("/api/me", headers=mine.headers)

    assert code_of(no_header) == "csrf_missing"
    assert code_of(no_cookie) == "invalid_refresh"
    assert me.status_code == 200


async def test_logout_all_ends_every_sign_in(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        first = await device(client)
        second = await device(client)
        response = await client.post("/api/auth/logout-all", headers=first.headers)
        answers = [
            await client.get("/api/me", headers=first.headers),
            await client.get("/api/me", headers=second.headers),
            await refresh(client, second.refresh_token),
        ]

    assert response.status_code == 204
    assert [answer.status_code for answer in answers] == [401] * 3
