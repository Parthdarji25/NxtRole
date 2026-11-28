"""Signing in, and what stops password guessing."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from argon2 import PasswordHasher
from sqlalchemy import update

from app.config import Settings
from app.core.logging import configure_logging
from app.users.models import User
from tests.conftest import unreachable_redis_url
from tests.integration.auth_helpers import (
    COOKIE,
    EMAIL,
    PASSWORD,
    api,
    code_of,
    from_address,
    make_user,
    reload_user,
    sign_in,
    stored_tokens,
)
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")


async def forget_locks(settings: Settings) -> None:
    """Moves time on past every lock: Redis keys gone, database lock in the past."""
    from app.core.redis import create_redis

    redis = create_redis(settings.redis_url.get_secret_value())
    await redis.flushdb()
    await redis.aclose()
    past = datetime.now(UTC) - timedelta(seconds=1)
    async with owner_session(settings) as session:
        await session.execute(
            update(User)
            .where(User.locked_until.is_not(None))
            .values(locked_until=past, last_failed_at=past - timedelta(minutes=15))
        )


async def test_auth_login_returns_a_token_and_a_protected_cookie(
    test_settings: Settings,
) -> None:
    account = await make_user(test_settings)

    async with api(test_settings) as client:
        response = await sign_in(client)
        body = response.json()
        me = await client.get(
            "/api/me", headers={"Authorization": f"Bearer {body['access_token']}"}
        )

    assert response.status_code == 200
    assert body["expires_in"] == 900
    assert body["user"] == {
        "id": str(account.user.id),
        "email": EMAIL,
        "display_name": None,
        "version": 1,
    }
    assert me.json()["email"] == EMAIL
    cookie = response.headers["set-cookie"].lower()
    for flag in ("httponly", "secure", "samesite=strict", "path=/api/auth", "max-age=604800"):
        assert flag in cookie, flag
    assert response.headers["cache-control"] == "no-store"
    # Only a hash of the refresh token is stored, with a shortened address.
    [row] = await stored_tokens(test_settings)
    assert response.cookies[COOKIE] != row.token_hash
    assert row.ip_hint == "198.51.100.0/24"


async def test_email_capitals_do_not_matter(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        response = await sign_in(client, email="Owner@EXAMPLE.com")

    assert response.status_code == 200


async def test_wrong_password_and_unknown_email_look_the_same(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        wrong = await sign_in(client, password="not the right password")
        unknown = await sign_in(client, email="nobody@example.com")

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert code_of(wrong) == "invalid_credentials"
    assert "set-cookie" not in wrong.headers


async def test_an_inactive_account_cannot_sign_in(test_settings: Settings) -> None:
    await make_user(test_settings)
    async with owner_session(test_settings) as session:
        await session.execute(update(User).values(is_active=False))

    async with api(test_settings) as client:
        response = await sign_in(client)

    assert code_of(response) == "invalid_credentials"


@pytest.mark.parametrize("email", [EMAIL, "nobody@example.com"])
async def test_auth_lockout_after_five_failures(email: str, test_settings: Settings) -> None:
    """Also true for an email with no account, so the lock reveals nothing (E-26)."""
    await make_user(test_settings)

    async with api(test_settings) as client:
        answers = [await sign_in(client, email, "wrong password!!") for _ in range(5)]
        sixth = await sign_in(client, email, PASSWORD)

    assert [code_of(answer) for answer in answers] == ["invalid_credentials"] * 4 + [
        "account_locked"
    ]
    assert sixth.status_code == 429
    assert code_of(sixth) == "account_locked"
    assert 0 < int(sixth.headers["retry-after"]) <= 900
    assert "15 minutes" in sixth.json()["detail"]["message"]


async def test_a_stranger_cannot_lock_the_owner_out_of_another_network(
    test_settings: Settings,
) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        for _ in range(6):
            await sign_in(client, password="wrong password!!", ip="203.0.113.66")
        owner = await sign_in(client, ip="198.51.100.1")

    assert owner.status_code == 200


async def test_the_lock_ends_after_its_time(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        for _ in range(5):
            await sign_in(client, password="wrong password!!")
        await forget_locks(test_settings)
        later = await sign_in(client)

    assert later.status_code == 200


@pytest.mark.parametrize("email", [EMAIL, "nobody@example.com"])
async def test_twenty_failures_from_anywhere_lock_the_email(
    email: str, test_settings: Settings
) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        for attempt in range(20):
            last = await sign_in(client, email, "wrong password!!", ip=f"203.0.113.{attempt}")
        fresh_address = await sign_in(client, email, PASSWORD, ip="198.51.100.200")
        await forget_locks(test_settings)
        later = await sign_in(client, email, PASSWORD, ip="198.51.100.200")

    assert code_of(last) == "account_locked"
    assert code_of(fresh_address) == "account_locked"
    assert later.status_code == (200 if email == EMAIL else 401)


async def test_parallel_wrong_attempts_are_all_counted(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        await asyncio.gather(
            *(
                sign_in(client, password="wrong password!!", ip=f"203.0.113.{attempt}")
                for attempt in range(12)
            )
        )

    assert (await reload_user(test_settings)).failed_logins == 12


async def test_a_correct_password_forgets_earlier_mistakes(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        for _ in range(4):
            await sign_in(client, password="wrong password!!")
        await sign_in(client)
        counted = (await reload_user(test_settings)).failed_logins
        after = [await sign_in(client, password="wrong password!!") for _ in range(4)]

    assert counted == 0
    assert {code_of(answer) for answer in after} == {"invalid_credentials"}


async def test_too_many_attempts_from_one_address_are_slowed(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings, login_rate_per_minute=5) as client:
        # Different emails, so that no account lock gets involved.
        for number in range(5):
            await sign_in(client, email=f"person{number}@example.com")
        sixth = await sign_in(client)
        elsewhere = await sign_in(client, ip="198.51.100.99")

    assert sixth.status_code == 429
    assert code_of(sixth) == "rate_limited"
    assert 0 < int(sixth.headers["retry-after"]) <= 60
    assert sixth.headers["ratelimit-remaining"] == "0"
    assert elsewhere.status_code == 200


async def test_an_invented_forwarding_address_does_not_escape_the_limit(
    test_settings: Settings,
) -> None:
    async with api(test_settings, login_rate_per_minute=2) as client:
        answers = [
            await client.post(
                "/api/auth/login",
                json={"email": f"p{number}@example.com", "password": PASSWORD},
                # The visitor adds a made-up entry; our forwarder appends the real one.
                headers=from_address(f"10.0.0.{number}, 203.0.113.5"),
            )
            for number in range(3)
        ]

    assert code_of(answers[2]) == "rate_limited"


async def test_redis_down_behaviour_still_signs_in_and_still_locks(
    test_settings: Settings,
) -> None:
    """E-62: without Redis the database counts, and locks after five."""
    await make_user(test_settings)
    from pydantic import SecretStr

    broken = SecretStr(unreachable_redis_url())

    async with api(test_settings, redis_url=broken, login_rate_per_minute=1) as client:
        first = await sign_in(client)
        second = await sign_in(client)
        failures = [await sign_in(client, password="wrong password!!") for _ in range(5)]
        correct = await sign_in(client)

    assert first.status_code == second.status_code == 200
    assert code_of(failures[3]) == "invalid_credentials"
    assert code_of(failures[4]) == "account_locked"
    assert code_of(correct) == "account_locked"
    locked_until = (await reload_user(test_settings)).locked_until
    assert locked_until is not None and locked_until > datetime.now(UTC)


@pytest.mark.parametrize(
    "body",
    [
        {"email": EMAIL, "password": "x" * 129},
        {"email": "a" * 250 + "@example.com", "password": PASSWORD},
        {"email": EMAIL, "password": PASSWORD, "admin": True},
        {"email": "not-an-email", "password": PASSWORD},
        {"email": EMAIL},
    ],
)
async def test_bad_input_is_refused_before_any_work_and_not_echoed(
    body: dict[str, object], test_settings: Settings
) -> None:
    async with api(test_settings) as client:
        response = await client.post("/api/auth/login", json=body)

    assert response.status_code == 422
    assert code_of(response) == "validation_error"
    assert PASSWORD not in response.text
    assert "xxxxxxxxxx" not in response.text


async def test_an_old_weaker_hash_is_upgraded_at_sign_in(test_settings: Settings) -> None:
    await make_user(test_settings)
    old = PasswordHasher(time_cost=2, memory_cost=8_192, parallelism=1).hash(PASSWORD)
    async with owner_session(test_settings) as session:
        await session.execute(update(User).values(password_hash=old))

    async with api(test_settings) as client:
        assert (await sign_in(client)).status_code == 200
        again = await sign_in(client)

    assert (await reload_user(test_settings)).password_hash != old
    assert again.status_code == 200


async def test_nothing_secret_reaches_the_logs(
    test_settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        configure_logging("DEBUG")
        signed_in = await sign_in(client)
        await sign_in(client, password="wrong password!!")
        token = signed_in.json()["access_token"]
        await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    output = capsys.readouterr().out
    configure_logging("INFO")
    assert "signed_in" in output
    for secret in (PASSWORD, "wrong password!!", token, signed_in.cookies[COOKIE], EMAIL):
        assert secret not in output
