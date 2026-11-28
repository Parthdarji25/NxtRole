from collections.abc import Iterator

import pytest
from sqlalchemy import select

from app.auth import admin, passwords, repository
from app.auth.models import RefreshToken
from app.config import Settings
from app.users.models import User
from tests.integration.factories import owner_session

PASSWORD = "a long quiet evening in pune"
NEW_PASSWORD = "the second long password here"


class Script(admin.Terminal):
    """Answers the command's questions and remembers what it says."""

    def __init__(self, *answers: str) -> None:
        waiting: Iterator[str] = iter(answers)
        said: list[str] = []
        super().__init__(
            ask=lambda _question: next(waiting),
            ask_secret=lambda _question: next(waiting),
            say=said.append,
        )
        object.__setattr__(self, "said", said)

    @property
    def output(self) -> str:
        return "\n".join(self.said)  # type: ignore[attr-defined]


async def users(settings: Settings) -> list[User]:
    async with owner_session(settings) as session:
        return list((await session.scalars(select(User))).all())


def recovery_code_in(output: str) -> str:
    return next(line.strip() for line in output.splitlines() if line.startswith("    "))


async def create(settings: Settings, email: str = "Owner@Example.com") -> Script:
    terminal = Script(email, PASSWORD, PASSWORD)
    await admin.create_owner(settings, terminal)
    return terminal


async def test_create_owner_stores_hashes_and_shows_the_code_once(
    test_settings: Settings,
) -> None:
    terminal = await create(test_settings)

    [user] = await users(test_settings)
    assert user.email == "owner@example.com"
    assert await passwords.verify_password(user.password_hash, PASSWORD)
    code = recovery_code_in(terminal.output)
    assert await passwords.verify_recovery_code(user.recovery_code_hash, code)
    assert PASSWORD not in terminal.output
    assert code not in user.recovery_code_hash


async def test_create_owner_refuses_a_second_account(test_settings: Settings) -> None:
    await create(test_settings)

    with pytest.raises(admin.CommandError, match="already exists"):
        await admin.create_owner(test_settings, Script("other@example.com", PASSWORD, PASSWORD))

    assert len(await users(test_settings)) == 1


@pytest.mark.parametrize(
    ("answers", "message"),
    [
        (("not-an-email",), "valid email"),
        (("owner@example.com", "short"), "at least 12"),
        (("owner@example.com", PASSWORD, "different password"), "not the same"),
    ],
)
async def test_create_owner_explains_bad_input_and_creates_nothing(
    test_settings: Settings, answers: tuple[str, ...], message: str
) -> None:
    with pytest.raises(admin.CommandError, match=message):
        await admin.create_owner(test_settings, Script(*answers))

    assert await users(test_settings) == []


async def test_reset_password_changes_both_secrets_and_signs_everyone_out(
    test_settings: Settings,
) -> None:
    old_code = recovery_code_in((await create(test_settings)).output)
    await add_session(test_settings)

    terminal = Script(NEW_PASSWORD, NEW_PASSWORD)
    await admin.reset_password(test_settings, terminal)

    [user] = await users(test_settings)
    assert await passwords.verify_password(user.password_hash, NEW_PASSWORD)
    assert not await passwords.verify_recovery_code(user.recovery_code_hash, old_code)
    async with owner_session(test_settings) as session:
        assert await repository.active_sessions(session, user.id) == []


async def add_session(settings: Settings) -> str:
    """A signed-in device, as signing in would leave it."""
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    family = uuid4()
    [user] = await users(settings)
    async with owner_session(settings) as session:
        session.add(
            RefreshToken(
                user_id=user.id,
                family_id=family,
                token_hash=uuid4().hex,
                expires_at=datetime.now(UTC) + timedelta(days=1),
                user_agent="Test browser",
                ip_hint="127.0.0.0/24",
            )
        )
    return str(family)


async def test_list_and_revoke_sessions(test_settings: Settings) -> None:
    await create(test_settings)
    first, second = await add_session(test_settings), await add_session(test_settings)

    listed = Script()
    await admin.list_sessions(test_settings, listed)
    await admin.revoke_sessions(test_settings, Script(), only=first)
    after_one = Script()
    await admin.list_sessions(test_settings, after_one)
    await admin.revoke_sessions(test_settings, Script())
    after_all = Script()
    await admin.list_sessions(test_settings, after_all)

    assert first in listed.output and second in listed.output
    assert "Test browser" in listed.output
    assert first not in after_one.output and second in after_one.output
    assert "No device is signed in." in after_all.output


@pytest.mark.parametrize("session_id", ["nonsense", "00000000-0000-0000-0000-000000000000"])
async def test_revoking_an_unknown_session_says_so(
    test_settings: Settings, session_id: str
) -> None:
    await create(test_settings)

    with pytest.raises(admin.CommandError):
        await admin.revoke_sessions(test_settings, Script(), only=session_id)


async def test_commands_explain_that_no_account_exists(test_settings: Settings) -> None:
    with pytest.raises(admin.CommandError, match="create-owner"):
        await admin.list_sessions(test_settings, Script())
