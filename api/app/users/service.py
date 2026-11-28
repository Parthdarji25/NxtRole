"""The rules for the signed-in owner's account."""

import uuid

from redis.asyncio import Redis

from app.auth import passwords, repository
from app.auth.service import invalid_credentials
from app.core.deps import SignedInUser
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit

PASSWORD_ATTEMPTS_PER_MINUTE = 5


async def change_password(
    current: SignedInUser, redis: Redis, current_password: str, new_password: str
) -> None:
    """Changes the password and signs out every other device (FR-009)."""
    await enforce_rate_limit(
        redis, f"rate:password:{current.user.id}", PASSWORD_ATTEMPTS_PER_MINUTE, 60
    )
    if not await passwords.verify_password(current.user.password_hash, current_password):
        raise invalid_credentials()
    passwords.check_new_password(new_password, current.user.email)
    if passwords.normalise_password(new_password) == passwords.normalise_password(current_password):
        raise AppError("weak_password", "Choose a password you are not using now.", status_code=422)
    current.user.password_hash = await passwords.hash_password(new_password)
    await repository.revoke_all(current.db, current.user.id, keep_family=current.session_id)


async def sign_out_everywhere(current: SignedInUser) -> None:
    await repository.revoke_all(current.db, current.user.id)


async def sign_out_other_devices(current: SignedInUser) -> None:
    await repository.revoke_all(current.db, current.user.id, keep_family=current.session_id)


async def sign_out_device(current: SignedInUser, family_id: uuid.UUID) -> None:
    if not await repository.revoke_family(current.db, current.user.id, family_id):
        raise AppError("not_found", "That device is not signed in.", status_code=404)
