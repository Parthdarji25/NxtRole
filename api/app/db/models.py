"""Imports every model, so that migrations and tests know all the tables."""

from app.auth.models import RefreshToken
from app.core.idempotency import IdempotencyKey
from app.history.models import Event, Proposal
from app.users.models import User

__all__ = ["Event", "IdempotencyKey", "Proposal", "RefreshToken", "User"]
