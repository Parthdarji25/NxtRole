"""The two tokens (D-032).

Access token: a signed note (JWT) saying who you are, valid 15 minutes. Anyone can read it,
nobody can change it without the secret. Refresh token: 32 random bytes with no meaning,
valid 7 days; only its hash is stored.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.errors import AppError

ALGORITHM = "HS256"
ACCESS_LIFETIME = timedelta(minutes=15)
REFRESH_LIFETIME = timedelta(days=7)
# How much the clocks of two computers may differ.
LEEWAY = timedelta(seconds=30)
REQUIRED_CLAIMS = ["sub", "exp", "iat", "jti", "type", "sid"]


@dataclass(frozen=True)
class Identity:
    user_id: uuid.UUID
    # The sign-in this token belongs to (the refresh token family).
    session_id: uuid.UUID


def unauthorized() -> AppError:
    return AppError("unauthorized", "Sign in to continue.", status_code=401)


def create_access_token(identity: Identity, secret: str, now: datetime | None = None) -> str:
    issued = now or datetime.now(UTC)
    claims = {
        "sub": str(identity.user_id),
        "sid": str(identity.session_id),
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": issued,
        "exp": issued + ACCESS_LIFETIME,
    }
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def read_access_token(token: str, secret: str) -> Identity:
    try:
        claims = jwt.decode(
            token,
            secret,
            # Pinned: the token cannot choose how it is checked (blocks "alg": "none").
            algorithms=[ALGORITHM],
            leeway=LEEWAY,
            options={"require": REQUIRED_CLAIMS},
        )
        if claims["type"] != "access":
            raise unauthorized()
        return Identity(uuid.UUID(claims["sub"]), uuid.UUID(claims["sid"]))
    except jwt.ExpiredSignatureError:
        # The web app answers this one by quietly asking for a new access token.
        raise AppError("token_expired", "Your sign-in needs refreshing.", status_code=401) from None
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise unauthorized() from None


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    # A fast hash is enough here: the token is random and long, so it cannot be guessed.
    return hashlib.sha256(token.encode()).hexdigest()
