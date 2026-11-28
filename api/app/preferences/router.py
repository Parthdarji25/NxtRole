"""What the owner is looking for, under /api/preferences."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, SignedInUser
from app.history import service as history
from app.preferences.models import SearchPreferences
from app.preferences.schemas import Preferences, PreferencesSaved, SavePreferences, SetupStep
from app.preferences.target import current_values, row

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


async def shown(current: SignedInUser) -> Preferences:
    values = await current_values(current.db, current.user.id)
    stored = await row(current.db, current.user.id)
    return Preferences(
        **values.model_dump(),
        version=stored.version if stored else 0,
        onboarding_step=stored.onboarding_step if stored else 1,
    )


@router.get("", response_model=Preferences)
async def read(current: CurrentUser) -> Preferences:
    return await shown(current)


@router.put("", response_model=PreferencesSaved)
async def save(body: SavePreferences, current: CurrentUser) -> PreferencesSaved:
    """Saved with history, so it can be undone."""
    event = await history.apply_change(
        current.db,
        current.user.id,
        "preferences",
        current.user.id,
        body.model_dump(mode="json", exclude={"version"}),
        expected_version=body.version,
    )
    return PreferencesSaved(preferences=await shown(current), event_id=event.id if event else None)


@router.put("/setup-step", status_code=204)
async def remember_step(body: SetupStep, current: CurrentUser) -> None:
    """Where the owner stopped in setup (FR-020). Not part of history."""
    stored = await row(current.db, current.user.id)
    if stored is None:
        current.db.add(
            SearchPreferences(user_id=current.user.id, version=0, onboarding_step=body.step)
        )
    else:
        stored.onboarding_step = body.step
