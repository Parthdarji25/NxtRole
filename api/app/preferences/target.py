"""How the history engine reads and writes the preferences, including the rules they make."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.history.snapshot import Snapshot, not_found
from app.preferences.models import SearchPreferences
from app.preferences.schemas import WORK_MODES, PreferenceValues
from app.preferences.values import lakhs, rupees
from app.rules import repository as rules
from app.users import repository as users

PLAIN = ("titles", "places", "experience_min", "experience_max", "notice_days")


async def row(db: AsyncSession, user_id: uuid.UUID) -> SearchPreferences | None:
    return await db.get(SearchPreferences, user_id)


async def current_values(db: AsyncSession, user_id: uuid.UUID) -> PreferenceValues:
    """Each value is stored once: here from the preferences row and the owner's rules."""
    stored = await row(db, user_id)
    yours = await rules.yours(db, user_id)
    values: dict[str, Any] = {}
    if stored is not None:
        values = {name: getattr(stored, name) for name in PLAIN}
        if stored.expected_ctc_inr is not None:
            values["expected_ctc_lpa"] = lakhs(stored.expected_ctc_inr)
    if rules.MIN_FIXED_PAY in yours:
        values["min_salary_lpa"] = lakhs(yours[rules.MIN_FIXED_PAY].value["amount_inr"])
    if rules.WORK_MODES in yours:
        values["work_modes"] = yours[rules.WORK_MODES].value["modes"]
    if rules.EXCLUDE_COMPANY_TYPE in yours:
        values["avoid_company_types"] = yours[rules.EXCLUDE_COMPANY_TYPE].value["types"]
    return PreferenceValues.model_validate(values)


class PreferencesTarget:
    async def read(self, db: AsyncSession, user_id: uuid.UUID, target_id: uuid.UUID) -> Snapshot:
        if target_id != user_id or await users.get(db, user_id, lock=True) is None:
            raise not_found()
        stored = await row(db, user_id)
        values = (await current_values(db, user_id)).model_dump(mode="json")
        return Snapshot(values, stored.version if stored else 0)

    async def write(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        values: dict[str, Any],
    ) -> None:
        if target_id != user_id:
            raise not_found()
        wanted = PreferenceValues.model_validate(values)
        stored = await row(db, user_id)
        if stored is None:
            stored = SearchPreferences(user_id=user_id, version=0, onboarding_step=1)
            db.add(stored)
        for name in PLAIN:
            setattr(stored, name, getattr(wanted, name))
        stored.expected_ctc_inr = (
            rupees(wanted.expected_ctc_lpa) if wanted.expected_ctc_lpa is not None else None
        )
        stored.version += 1

        await rules.set_yours(
            db,
            user_id,
            rules.MIN_FIXED_PAY,
            {"amount_inr": rupees(wanted.min_salary_lpa)}
            if wanted.min_salary_lpa is not None
            else None,
        )
        # Accepting every work style hides nothing, so it is not a rule.
        await rules.set_yours(
            db,
            user_id,
            rules.WORK_MODES,
            {"modes": wanted.work_modes} if set(wanted.work_modes) != set(WORK_MODES) else None,
        )
        await rules.set_yours(
            db,
            user_id,
            rules.EXCLUDE_COMPANY_TYPE,
            {"types": wanted.avoid_company_types} if wanted.avoid_company_types else None,
        )
