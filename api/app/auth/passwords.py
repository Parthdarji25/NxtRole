"""Passwords and recovery codes. Only a one-way Argon2id "hash" of each is ever stored.

A hash can check a password but cannot be turned back into it. Hashing is deliberately slow,
so that someone with a copy of the database can try only a few guesses a second.
"""

import asyncio
import base64
import secrets
import unicodedata
from functools import lru_cache
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.errors import AppError

MIN_LENGTH = 12
# A limit before hashing, so a huge input cannot be used to slow the server down.
MAX_LENGTH = 128

COMMON_PASSWORDS_FILE = (
    Path(__file__).resolve().parent / "data" / "common_passwords_ncsc_2026-11-27.txt"
)

# 64 MiB of memory, 3 passes, 1 lane: about 0.3 seconds on the development laptop.
# Re-measured on the hosting platform at deployment (docs/SECURITY.md). Old hashes carry
# their own settings and are upgraded at the next sign-in.
HASHER = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=1)

RECOVERY_CODE_BYTES = 16


def normalise_password(password: str) -> str:
    """The same characters typed on different keyboards become the same bytes (NIST 800-63B).
    Spaces are kept: they are part of the password."""
    return unicodedata.normalize("NFKC", password)


@lru_cache
def common_passwords() -> frozenset[str]:
    lines = COMMON_PASSWORDS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(line for line in lines if line and not line.startswith("#"))


def check_new_password(password: str, email: str) -> None:
    """Rules for a new password: long enough, not a well-known one. No symbol rules."""
    normalised = normalise_password(password)
    problem = None
    if len(normalised) < MIN_LENGTH:
        problem = f"Use at least {MIN_LENGTH} characters. A short sentence works well."
    elif len(normalised) > MAX_LENGTH:
        problem = f"Use at most {MAX_LENGTH} characters."
    elif normalised.casefold() in common_passwords():
        problem = "That password is on a list of common passwords. Choose another."
    elif normalised.casefold() == email.casefold():
        problem = "Your password cannot be your email address."
    elif len(set(normalised)) < 5:
        problem = "Use more different characters."
    if problem:
        raise AppError("weak_password", problem, status_code=422)


async def hash_password(password: str) -> str:
    # In a thread, so that other requests are served while this one is being worked out.
    return await asyncio.to_thread(HASHER.hash, normalise_password(password))


def _matches(stored_hash: str, password: str) -> bool:
    try:
        return HASHER.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


async def verify_password(stored_hash: str, password: str) -> bool:
    return await asyncio.to_thread(_matches, stored_hash, normalise_password(password))


def needs_rehash(stored_hash: str) -> bool:
    return HASHER.check_needs_rehash(stored_hash)


@lru_cache
def _dummy_hash() -> str:
    return HASHER.hash(secrets.token_urlsafe(32))


async def verify_against_nothing(password: str) -> None:
    """Spends the same time as a real check, for an email that has no account, so that the
    speed of the answer does not reveal which emails exist."""
    dummy = await asyncio.to_thread(_dummy_hash)
    await verify_password(dummy, password)


def new_recovery_code() -> str:
    """A random 128-bit code in groups of four letters and digits, easy to copy by hand."""
    code = base64.b32encode(secrets.token_bytes(RECOVERY_CODE_BYTES)).decode().rstrip("=")
    return "-".join(code[start : start + 4] for start in range(0, len(code), 4))


def normalise_recovery_code(code: str) -> str:
    """Capitals, spaces and dashes do not matter when typing a recovery code."""
    return "".join(character for character in code.upper() if character.isalnum())


async def hash_recovery_code(code: str) -> str:
    return await hash_password(normalise_recovery_code(code))


async def verify_recovery_code(stored_hash: str, code: str) -> bool:
    return await verify_password(stored_hash, normalise_recovery_code(code))
