"""The rules of signing in, staying signed in and recovering access (D-032, D-050).

Counting a wrong password and ending a stolen sign-in must be saved even though the request
then fails, so these functions manage their own transactions and raise errors afterwards.
Password checks happen outside a transaction, because they are slow on purpose.
"""

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.auth import lockout, passwords, repository, tokens
from app.auth.models import RefreshToken
from app.config import Settings
from app.core.client_ip import ip_hint
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.db.session import set_current_user
from app.users import repository as users
from app.users.models import User

# Two tabs may refresh at the same moment; the loser's token was used only just now.
REUSE_GRACE = timedelta(seconds=10)
RATE_WINDOW_SECONDS = 60
MAX_USER_AGENT = 300

log = structlog.get_logger("nxtrole.auth")


@dataclass(frozen=True)
class Visitor:
    ip: str
    user_agent: str | None = None


@dataclass(frozen=True)
class Granted:
    access_token: str
    # None when the browser already holds the newest refresh token (the two-tab case).
    refresh_token: str | None


def invalid_credentials() -> AppError:
    return AppError("invalid_credentials", "That email or password is not right.", status_code=401)


def invalid_recovery() -> AppError:
    return AppError(
        "invalid_recovery", "That email or recovery code is not right.", status_code=401
    )


def account_locked(seconds: int) -> AppError:
    minutes = max(1, math.ceil(seconds / 60))
    unit = "minute" if minutes == 1 else "minutes"
    return AppError(
        "account_locked",
        f"Too many wrong attempts. Try again in {minutes} {unit}.",
        status_code=429,
        headers={"Retry-After": str(seconds)},
        extra={"retry_after_seconds": seconds},
    )


def invalid_refresh() -> AppError:
    return AppError("invalid_refresh", "Your sign-in has ended. Sign in again.", status_code=401)


def session_reused() -> AppError:
    return AppError(
        "session_reused",
        "This sign-in was used twice, so it was ended to keep you safe. Sign in again.",
        status_code=401,
    )


def seconds_until(moment: datetime | None) -> int:
    if moment is None:
        return 0
    return max(0, math.ceil((moment - datetime.now(UTC)).total_seconds()))


class AuthService:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], redis: Redis, settings: Settings
    ) -> None:
        self.sessions = sessions
        self.redis = redis
        self.secret = settings.require_jwt_secret()
        self.rate_per_minute = settings.login_rate_per_minute

    # --- Signing in ---------------------------------------------------------------------

    async def login(self, email: str, password: str, visitor: Visitor) -> tuple[Granted, User]:
        email = email.lower()
        await self._check_may_try(email, visitor, "login")
        user = await self._find(email)
        if user is not None and seconds_until(user.locked_until):
            raise account_locked(seconds_until(user.locked_until))

        if user is None or not user.is_active:
            await passwords.verify_against_nothing(password)
            correct = False
        else:
            correct = await passwords.verify_password(user.password_hash, password)
        if user is None or not correct:
            await self._count_failure(email, visitor, user)
            raise invalid_credentials()

        upgraded = (
            await passwords.hash_password(password)
            if passwords.needs_rehash(user.password_hash)
            else None
        )
        async with self.sessions.begin() as db:
            await set_current_user(db, user.id)
            await users.clear_failed_logins(db, user.id)
            if upgraded:
                await db.execute(
                    update(User).where(User.id == user.id).values(password_hash=upgraded)
                )
            await repository.delete_old(db, user.id)
            family_id = uuid.uuid4()
            refresh_token = self._add_token(db, user.id, family_id, visitor)
        await lockout.clear_after_success(self.redis, email, visitor.ip)
        log.info("signed_in")
        return self._grant(user.id, family_id, refresh_token), user

    # --- Staying signed in --------------------------------------------------------------

    async def refresh(self, refresh_token: str | None, visitor: Visitor) -> Granted:
        if not refresh_token:
            raise invalid_refresh()
        token_hash = tokens.hash_refresh_token(refresh_token)
        problem: AppError | None = None
        granted: Granted | None = None
        async with self.sessions.begin() as db:
            user_id = await repository.user_id_for_token(db, token_hash)
            if user_id is None:
                raise invalid_refresh()
            await set_current_user(db, user_id)
            row = await repository.lock_token(db, user_id, token_hash)
            user = await users.get(db, user_id)
            now = datetime.now(UTC)
            if row is None or user is None or not user.is_active:
                problem = invalid_refresh()
            elif row.revoked_at is not None:
                problem = session_reused()
            elif row.expires_at <= now:
                problem = invalid_refresh()
            elif row.used_at is None:
                row.used_at = now
                replacement = self._add_token(db, user_id, row.family_id, visitor)
                granted = self._grant(user_id, row.family_id, replacement)
            elif now - row.used_at <= REUSE_GRACE:
                granted = self._grant(user_id, row.family_id, None)
            else:
                # An old token came back: someone else may hold a copy. End the sign-in.
                await repository.revoke_family(db, user_id, row.family_id)
                log.warning("refresh_token_reused")
                problem = session_reused()
        if granted is None:
            raise problem or invalid_refresh()
        return granted

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            raise invalid_refresh()
        token_hash = tokens.hash_refresh_token(refresh_token)
        async with self.sessions.begin() as db:
            user_id = await repository.user_id_for_token(db, token_hash)
            if user_id is None:
                raise invalid_refresh()
            await set_current_user(db, user_id)
            row = await repository.lock_token(db, user_id, token_hash)
            if row is None:
                raise invalid_refresh()
            await repository.revoke_family(db, user_id, row.family_id)

    # --- Forgotten password -------------------------------------------------------------

    async def recover(self, email: str, code: str, new_password: str, visitor: Visitor) -> str:
        """Sets a new password with the recovery code. Returns the next recovery code."""
        email = email.lower()
        await self._check_may_try(email, visitor, "recover")
        # Checked first: it depends only on what was typed, so it reveals nothing.
        passwords.check_new_password(new_password, email)
        user = await self._find(email)
        if user is not None and seconds_until(user.locked_until):
            raise account_locked(seconds_until(user.locked_until))

        if user is None or not user.is_active:
            await passwords.verify_against_nothing(code)
            correct = False
        else:
            correct = await passwords.verify_recovery_code(user.recovery_code_hash, code)
        if user is None or not correct:
            await self._count_failure(email, visitor, user)
            raise invalid_recovery()

        next_code = passwords.new_recovery_code()
        password_hash = await passwords.hash_password(new_password)
        code_hash = await passwords.hash_recovery_code(next_code)
        async with self.sessions.begin() as db:
            await set_current_user(db, user.id)
            # Only if the code is still the one that was checked: it works once.
            changed = await db.scalar(
                update(User)
                .where(User.id == user.id, User.recovery_code_hash == user.recovery_code_hash)
                .values(password_hash=password_hash, recovery_code_hash=code_hash)
                .returning(User.id)
            )
            if changed is None:
                raise invalid_recovery()
            await users.clear_failed_logins(db, user.id)
            await repository.revoke_all(db, user.id)
        await lockout.unlock(self.redis, email)
        log.info("access_recovered")
        return next_code

    # --- Shared steps -------------------------------------------------------------------

    async def _check_may_try(self, email: str, visitor: Visitor, action: str) -> None:
        locked = await lockout.locked_seconds(self.redis, email, visitor.ip)
        if locked:
            raise account_locked(locked)
        await enforce_rate_limit(
            self.redis, f"rate:{action}:{visitor.ip}", self.rate_per_minute, RATE_WINDOW_SECONDS
        )

    async def _find(self, email: str) -> User | None:
        async with self.sessions.begin() as db:
            user_id = await users.id_for_email(db, email)
            if user_id is None:
                return None
            await set_current_user(db, user_id)
            return await users.get(db, user_id)

    async def _count_failure(self, email: str, visitor: Visitor, user: User | None) -> None:
        """Counts a wrong attempt and raises `account_locked` if it caused a lock."""
        lock = await lockout.record_failure(self.redis, email, visitor.ip)
        seconds = lock or 0
        if user is not None:
            # Without Redis the database alone must stop guessing, so it locks sooner.
            threshold = lockout.PAIR_LIMIT if lock is None else lockout.ACCOUNT_LIMIT
            async with self.sessions.begin() as db:
                await set_current_user(db, user.id)
                locked_until = await users.record_failed_login(
                    db, user.id, threshold, lockout.WINDOW
                )
            seconds = max(seconds, seconds_until(locked_until))
        log.info("wrong_sign_in_attempt", locked=bool(seconds))
        if seconds:
            raise account_locked(seconds)

    def _add_token(
        self, db: AsyncSession, user_id: uuid.UUID, family_id: uuid.UUID, visitor: Visitor
    ) -> str:
        refresh_token = tokens.new_refresh_token()
        db.add(
            RefreshToken(
                user_id=user_id,
                family_id=family_id,
                token_hash=tokens.hash_refresh_token(refresh_token),
                expires_at=datetime.now(UTC) + tokens.REFRESH_LIFETIME,
                user_agent=(visitor.user_agent or "")[:MAX_USER_AGENT] or None,
                ip_hint=ip_hint(visitor.ip),
            )
        )
        return refresh_token

    def _grant(
        self, user_id: uuid.UUID, family_id: uuid.UUID, refresh_token: str | None
    ) -> Granted:
        identity = tokens.Identity(user_id, family_id)
        return Granted(tokens.create_access_token(identity, self.secret), refresh_token)
