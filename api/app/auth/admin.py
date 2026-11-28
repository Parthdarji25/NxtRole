"""Account commands run by the owner in a terminal (D-027). There is no public sign-up.

They connect as the database owner. Passwords are typed into the terminal without being
shown, and are never accepted as command-line words (which other programs could read).
"""

import getpass
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import lockout, passwords, repository
from app.config import Settings
from app.core.errors import AppError
from app.core.redis import create_redis
from app.db.session import create_engine, create_session_factory
from app.users import repository as users
from app.users.models import User

IST = ZoneInfo("Asia/Kolkata")
EMAIL = TypeAdapter(EmailStr)


@dataclass(frozen=True)
class Terminal:
    """How a command talks to the person. Tests supply their own."""

    ask: Callable[[str], str] = input
    ask_secret: Callable[[str], str] = getpass.getpass
    say: Callable[[str], None] = print


class CommandError(Exception):
    """A problem to show to the person, in plain words."""


@asynccontextmanager
async def owner_transaction(settings: Settings) -> AsyncIterator[AsyncSession]:
    engine = create_engine(settings.require_migration_database_url())
    try:
        async with create_session_factory(engine).begin() as session:
            yield session
    finally:
        await engine.dispose()


def clean_email(value: str) -> str:
    try:
        return EMAIL.validate_python(value.strip()).lower()
    except ValidationError:
        raise CommandError("That is not a valid email address.") from None


def ask_new_password(terminal: Terminal, email: str) -> str:
    password = terminal.ask_secret(
        f"New password (at least {passwords.MIN_LENGTH} characters, not shown as you type): "
    )
    try:
        passwords.check_new_password(password, email)
    except AppError as error:
        raise CommandError(error.message) from None
    if terminal.ask_secret("The same password again: ") != password:
        raise CommandError("The two passwords are not the same. Nothing was changed.")
    return password


def show_recovery_code(terminal: Terminal, code: str) -> None:
    terminal.say("")
    terminal.say("Your recovery code (shown only this once):")
    terminal.say("")
    terminal.say(f"    {code}")
    terminal.say("")
    terminal.say("Write it on paper or save it in a password manager. If you forget your")
    terminal.say("password, this code at /login/recover is how you get back in.")


async def create_owner(settings: Settings, terminal: Terminal) -> None:
    async with owner_transaction(settings) as session:
        if await session.scalar(select(func.count()).select_from(User)):
            raise CommandError(
                "An account already exists. To change its password: "
                "uv run python -m app.cli reset-password"
            )
        email = clean_email(terminal.ask("Your email address: "))
        password = ask_new_password(terminal, email)
        code = passwords.new_recovery_code()
        session.add(
            User(
                email=email,
                password_hash=await passwords.hash_password(password),
                recovery_code_hash=await passwords.hash_recovery_code(code),
            )
        )
    terminal.say("Account created.")
    show_recovery_code(terminal, code)


async def the_user(session: AsyncSession, terminal: Terminal) -> User:
    """The only account, or the one the person names if there are several."""
    found = (await session.scalars(select(User).limit(2))).all()
    if not found:
        raise CommandError("There is no account yet: uv run python -m app.cli create-owner")
    if len(found) == 1:
        return found[0]
    email = clean_email(terminal.ask("Email address of the account: "))
    user = (await session.scalars(select(User).where(User.email == email))).one_or_none()
    if user is None:
        raise CommandError("There is no account with that email address.")
    return user


async def reset_password(settings: Settings, terminal: Terminal) -> None:
    async with owner_transaction(settings) as session:
        user = await the_user(session, terminal)
        password = ask_new_password(terminal, user.email)
        code = passwords.new_recovery_code()
        user.password_hash = await passwords.hash_password(password)
        user.recovery_code_hash = await passwords.hash_recovery_code(code)
        await users.clear_failed_logins(session, user.id)
        await repository.revoke_all(session, user.id)
        email = user.email
    redis = create_redis(settings.redis_url.get_secret_value())
    await lockout.unlock(redis, email)
    await redis.aclose()
    terminal.say("Password changed. Every device has been signed out.")
    show_recovery_code(terminal, code)


async def list_sessions(settings: Settings, terminal: Terminal) -> None:
    async with owner_transaction(settings) as session:
        user = await the_user(session, terminal)
        sessions = await repository.active_sessions(session, user.id)
    if not sessions:
        terminal.say("No device is signed in.")
    for entry in sessions:
        used = entry.last_used_at.astimezone(IST).strftime("%d %b %Y %H:%M IST")
        terminal.say(f"{entry.family_id}  last used {used}")
        terminal.say(f"    {entry.user_agent or 'unknown device'}  {entry.ip_hint or ''}".rstrip())


async def revoke_sessions(settings: Settings, terminal: Terminal, only: str | None = None) -> None:
    async with owner_transaction(settings) as session:
        user = await the_user(session, terminal)
        if only is None:
            await repository.revoke_all(session, user.id)
        else:
            try:
                family_id = uuid.UUID(only)
            except ValueError:
                raise CommandError("That is not a session id. See list-sessions.") from None
            if not await repository.revoke_family(session, user.id, family_id):
                raise CommandError("No signed-in device has that id. See list-sessions.")
    terminal.say("Signed out every device." if only is None else "That device was signed out.")
