"""Recovery, changing the password, and the list of signed-in devices."""

import uuid

import pytest

from app.auth import passwords
from app.config import Settings
from tests.integration.auth_helpers import (
    EMAIL,
    NEW_PASSWORD,
    PASSWORD,
    api,
    code_of,
    device,
    from_address,
    make_user,
    refresh,
    reload_user,
    sign_in,
)

pytestmark = pytest.mark.usefixtures("quick_hashing")


def recovery(code: str, email: str = EMAIL, password: str = NEW_PASSWORD) -> dict[str, str]:
    return {"email": email, "recovery_code": code, "new_password": password}


async def test_recover_with_code_rotates_code(test_settings: Settings) -> None:
    """E-25: no email service is needed."""
    account = await make_user(test_settings)

    async with api(test_settings) as client:
        old_device = await device(client)
        typed = account.recovery_code.lower().replace("-", " ")
        response = await client.post("/api/auth/recover", json=recovery(typed))
        old_session = await refresh(client, old_device.refresh_token)
        old_password = await sign_in(client)
        new_password = await sign_in(client, password=NEW_PASSWORD)
        reused = await client.post(
            "/api/auth/recover", json=recovery(account.recovery_code, password=PASSWORD)
        )

    assert response.status_code == 200
    next_code = response.json()["recovery_code"]
    assert next_code != account.recovery_code
    user = await reload_user(test_settings)
    assert await passwords.verify_recovery_code(user.recovery_code_hash, next_code)
    assert old_session.status_code == 401
    assert old_password.status_code == 401
    assert new_password.status_code == 200
    assert code_of(reused) == "invalid_recovery"


async def test_a_wrong_code_and_an_unknown_email_look_the_same(
    test_settings: Settings,
) -> None:
    account = await make_user(test_settings)

    async with api(test_settings) as client:
        wrong = await client.post("/api/auth/recover", json=recovery(passwords.new_recovery_code()))
        unknown = await client.post(
            "/api/auth/recover",
            json=recovery(account.recovery_code, email="nobody@example.com"),
        )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_a_weak_new_password_does_not_use_up_the_code(test_settings: Settings) -> None:
    account = await make_user(test_settings)

    async with api(test_settings) as client:
        weak = await client.post(
            "/api/auth/recover", json=recovery(account.recovery_code, password="short")
        )
        good = await client.post("/api/auth/recover", json=recovery(account.recovery_code))

    assert code_of(weak) == "weak_password"
    assert good.status_code == 200


async def test_guessing_recovery_codes_is_locked(test_settings: Settings) -> None:
    account = await make_user(test_settings)

    async with api(test_settings) as client:
        for _ in range(5):
            last = await client.post(
                "/api/auth/recover",
                json=recovery(passwords.new_recovery_code()),
                headers=from_address("203.0.113.1"),
            )
        right_code = await client.post(
            "/api/auth/recover",
            json=recovery(account.recovery_code),
            headers=from_address("203.0.113.1"),
        )

    assert code_of(last) == "account_locked"
    assert code_of(right_code) == "account_locked"


async def test_change_password_signs_out_the_other_devices(test_settings: Settings) -> None:
    """FR-009."""
    await make_user(test_settings)

    async with api(test_settings) as client:
        here = await device(client)
        elsewhere = await device(client)
        response = await client.post(
            "/api/account/password",
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
            headers=here.headers,
        )
        still_here = await client.get("/api/me", headers=here.headers)
        gone = await client.get("/api/me", headers=elsewhere.headers)
        old = await sign_in(client)
        new = await sign_in(client, password=NEW_PASSWORD)

    assert response.status_code == 204
    assert still_here.status_code == 200
    assert gone.status_code == 401
    assert (old.status_code, new.status_code) == (401, 200)


@pytest.mark.parametrize(
    ("current", "new", "code"),
    [
        ("not my password at all", NEW_PASSWORD, "invalid_credentials"),
        (PASSWORD, "short", "weak_password"),
        (PASSWORD, "password1234", "weak_password"),
        (PASSWORD, PASSWORD, "weak_password"),
    ],
)
async def test_a_refused_password_change_changes_nothing(
    current: str, new: str, code: str, test_settings: Settings
) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        here = await device(client)
        response = await client.post(
            "/api/account/password",
            json={"current_password": current, "new_password": new},
            headers=here.headers,
        )
        still = await sign_in(client)

    assert code_of(response) == code
    assert still.status_code == 200


async def test_password_changes_are_rate_limited(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        here = await device(client)
        body = {"current_password": "guessing the password", "new_password": NEW_PASSWORD}
        answers = [
            await client.post("/api/account/password", json=body, headers=here.headers)
            for _ in range(6)
        ]

    assert code_of(answers[5]) == "rate_limited"


async def test_devices_can_be_listed_and_signed_out(test_settings: Settings) -> None:
    await make_user(test_settings)

    async with api(test_settings) as client:
        here = await device(client)
        elsewhere = await device(client)
        await device(client)
        before = (await client.get("/api/account/sessions", headers=here.headers)).json()
        other_ids = [item["family_id"] for item in before["items"] if not item["current"]]

        one = await client.delete(f"/api/account/sessions/{other_ids[0]}", headers=here.headers)
        twice = await client.delete(f"/api/account/sessions/{other_ids[0]}", headers=here.headers)
        unknown = await client.delete(f"/api/account/sessions/{uuid.uuid4()}", headers=here.headers)
        rest = await client.delete("/api/account/sessions", headers=here.headers)
        after = (await client.get("/api/account/sessions", headers=here.headers)).json()
        gone = await client.get("/api/me", headers=elsewhere.headers)

    assert len(before["items"]) == 3
    assert sum(item["current"] for item in before["items"]) == 1
    assert before["items"][0]["ip_hint"] == "198.51.100.0/24"
    assert one.status_code == rest.status_code == 204
    assert twice.status_code == unknown.status_code == 404
    assert [item["current"] for item in after["items"]] == [True]
    assert gone.status_code == 401
