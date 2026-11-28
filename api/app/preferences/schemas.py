"""What the owner is looking for, as sent and stored."""

import uuid
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.preferences.values import clean_list, lakhs, normalise_place, rupees

WorkMode = Literal["remote", "hybrid", "onsite"]
WORK_MODES: tuple[WorkMode, ...] = ("remote", "hybrid", "onsite")

Item = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
# Pay in lakhs a year, such as 14 or 14.5.
Lakhs = Annotated[Decimal, Field(gt=0, le=1_000, max_digits=6, decimal_places=2)]


class PreferenceValues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titles: list[Item] = Field(default_factory=list, max_length=20)
    places: list[Item] = Field(default_factory=list, max_length=20)
    experience_min: int | None = Field(default=None, ge=0, le=50)
    experience_max: int | None = Field(default=None, ge=0, le=50)
    notice_days: int | None = Field(default=None, ge=0, le=365)
    expected_ctc_lpa: Lakhs | None = None
    # The three below hide jobs, so they are stored as rules (D-053).
    min_salary_lpa: Lakhs | None = None
    work_modes: list[WorkMode] = Field(default_factory=lambda: list(WORK_MODES), min_length=1)
    avoid_company_types: list[Item] = Field(default_factory=list, max_length=20)

    @field_validator("titles", "avoid_company_types")
    @classmethod
    def no_repeats(cls, values: list[str]) -> list[str]:
        return clean_list(values)

    @field_validator("min_salary_lpa", "expected_ctc_lpa")
    @classmethod
    def one_way_of_writing_pay(cls, value: Decimal | None) -> Decimal | None:
        # 14.50 and 14.5 are the same amount, and must compare as the same.
        return None if value is None else lakhs(rupees(value))

    @field_validator("places")
    @classmethod
    def one_name_per_city(cls, values: list[str]) -> list[str]:
        return clean_list([normalise_place(value) for value in values])

    @field_validator("work_modes")
    @classmethod
    def in_order(cls, values: list[WorkMode]) -> list[WorkMode]:
        return [mode for mode in WORK_MODES if mode in values]

    @model_validator(mode="after")
    def experience_range(self) -> Self:
        if (
            self.experience_min is not None
            and self.experience_max is not None
            and self.experience_min > self.experience_max
        ):
            raise ValueError("the least experience is more than the most")
        return self


class SavePreferences(PreferenceValues):
    # The version the change was based on.
    version: int = Field(ge=0)


class Preferences(PreferenceValues):
    version: int
    onboarding_step: int


class PreferencesSaved(BaseModel):
    preferences: Preferences
    event_id: uuid.UUID | None


class SetupStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=1, le=5)
