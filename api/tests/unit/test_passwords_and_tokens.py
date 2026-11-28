import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from argon2 import PasswordHasher

from app.auth import passwords, tokens
from app.core.errors import AppError

SECRET = "unit-test-signing-secret-0123456789abcdef"
EMAIL = "owner@example.com"


async def test_a_hash_checks_the_password_and_never_contains_it() -> None:
    stored = await passwords.hash_password("correct horse battery staple")

    assert stored.startswith("$argon2id$")
    assert "correct horse" not in stored
    assert await passwords.verify_password(stored, "correct horse battery staple")
    assert not await passwords.verify_password(stored, "correct horse battery stapler")
    assert not await passwords.verify_password("not a hash", "anything")


def test_hashing_is_at_least_the_recommended_minimum() -> None:
    # OWASP minimum for Argon2id: 19 MiB, 2 passes, 1 lane.
    assert passwords.HASHER.memory_cost >= 19_456
    assert passwords.HASHER.time_cost >= 2


async def test_weaker_old_hashes_are_marked_for_upgrade() -> None:
    old = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1).hash("some password here")

    assert passwords.needs_rehash(old)
    assert not passwords.needs_rehash(await passwords.hash_password("some password here"))


async def test_spaces_unicode_and_composed_characters_work() -> None:
    # The same name typed as one character or as a letter plus an accent mark.
    composed, decomposed = "  café with spaces नम  ", "  café with spaces नम  "
    stored = await passwords.hash_password(composed)

    assert await passwords.verify_password(stored, decomposed)
    assert not await passwords.verify_password(stored, composed.strip())


@pytest.mark.parametrize(
    ("password", "reason"),
    [
        ("elevenchars", "at least 12"),
        ("x" * 129, "at most 128"),
        ("Password1234", "common"),
        ("OWNER@example.com", "email"),
        ("zqzqzqzqzqzqzqzq", "different characters"),
    ],
)
def test_weak_new_passwords_are_refused_with_a_reason(password: str, reason: str) -> None:
    with pytest.raises(AppError, match=reason) as error:
        passwords.check_new_password(password, EMAIL)

    assert error.value.code == "weak_password"
    assert password not in error.value.message


def test_a_long_sentence_is_accepted() -> None:
    passwords.check_new_password("the river runs past my window", EMAIL)


def test_the_common_password_list_is_loaded() -> None:
    assert len(passwords.common_passwords()) > 1000
    assert all(len(word) >= passwords.MIN_LENGTH for word in passwords.common_passwords())


async def test_recovery_codes_are_random_and_forgiving_to_type() -> None:
    code = passwords.new_recovery_code()
    stored = await passwords.hash_recovery_code(code)

    assert code != passwords.new_recovery_code()
    assert len(passwords.normalise_recovery_code(code)) == 26
    assert await passwords.verify_recovery_code(stored, code.lower().replace("-", " "))
    assert not await passwords.verify_recovery_code(stored, passwords.new_recovery_code())


def identity() -> tokens.Identity:
    return tokens.Identity(uuid.uuid4(), uuid.uuid4())


def test_access_token_round_trip_and_claims() -> None:
    who = identity()
    token = tokens.create_access_token(who, SECRET)

    assert tokens.read_access_token(token, SECRET) == who
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert set(claims) == {"sub", "sid", "type", "jti", "iat", "exp"}
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_expired_token_says_so() -> None:
    old = datetime.now(UTC) - timedelta(minutes=16)

    with pytest.raises(AppError) as error:
        tokens.read_access_token(tokens.create_access_token(identity(), SECRET, old), SECRET)

    assert (error.value.code, error.value.status_code) == ("token_expired", 401)


def test_a_small_clock_difference_is_allowed() -> None:
    # Expired 10 seconds ago, and issued 10 seconds in the "future".
    for shift in (timedelta(minutes=-15, seconds=-10), timedelta(seconds=10)):
        issued = datetime.now(UTC) + shift
        tokens.read_access_token(tokens.create_access_token(identity(), SECRET, issued), SECRET)


def unsigned_token() -> str:
    def part(data: dict[str, object]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    now = int(datetime.now(UTC).timestamp())
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "type": "access",
        "jti": "x",
        "iat": now,
        "exp": now + 600,
    }
    return f"{part({'alg': 'none', 'typ': 'JWT'})}.{part(claims)}."


def signed(**changes: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "type": "access",
        "jti": "x",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(changes)
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, SECRET, "HS256")


@pytest.mark.parametrize(
    "token",
    [
        "",
        "not.a.token",
        unsigned_token(),
        signed(type="refresh"),
        signed(sid=None),
        signed(exp=None),
        signed(sub="not-a-uuid"),
        signed()[:-4] + "AAAA",
    ],
    ids=[
        "empty",
        "nonsense",
        "alg-none",
        "wrong-type",
        "no-session",
        "no-expiry",
        "bad-subject",
        "tampered",
    ],
)
def test_forged_or_broken_tokens_are_refused(token: str) -> None:
    with pytest.raises(AppError) as error:
        tokens.read_access_token(token, SECRET)

    assert (error.value.code, error.value.status_code) == ("unauthorized", 401)


def test_a_token_signed_with_another_secret_is_refused() -> None:
    token = tokens.create_access_token(identity(), SECRET[::-1])

    with pytest.raises(AppError, match="Sign in"):
        tokens.read_access_token(token, SECRET)


def test_refresh_tokens_are_long_random_and_hashed() -> None:
    first, second = tokens.new_refresh_token(), tokens.new_refresh_token()

    assert first != second
    assert len(first) >= 43
    assert len(tokens.hash_refresh_token(first)) == 64
    assert first not in tokens.hash_refresh_token(first)
