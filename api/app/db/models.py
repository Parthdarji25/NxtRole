"""Imports every model, so that migrations and tests know all the tables."""

from app.ai.usage import AiUsage
from app.auth.models import RefreshToken
from app.core.idempotency import IdempotencyKey
from app.files.models import File
from app.history.models import Event, Proposal
from app.preferences.models import SearchPreferences
from app.profile.models import ProfileVersion
from app.rules.models import Rule
from app.users.models import User
from app.worker.models import BackgroundJob

__all__ = [
    "AiUsage",
    "BackgroundJob",
    "Event",
    "File",
    "IdempotencyKey",
    "ProfileVersion",
    "Proposal",
    "RefreshToken",
    "Rule",
    "SearchPreferences",
    "User",
]
