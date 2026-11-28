"""The shapes of profile facts: what the AI may answer, and what is stored."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.ai.privacy import Identity

FactKind = Literal[
    "experience_years",
    "role",
    "achievement",
    "skill",
    "project",
    "education",
    "certification",
    "location",
    "notice_period",
]

MAX_FACTS = 300

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class ExtractedFact(BaseModel):
    """One fact as the AI answers it. Code checks it against the resume."""

    model_config = ConfigDict(extra="forbid")

    kind: FactKind
    value: str
    company: str | None
    dates: str | None
    quote: str


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[ExtractedFact]


class Fact(BaseModel):
    """One fact in the owner's profile."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    kind: FactKind
    value: Text
    company: Short | None = None
    dates: Short | None = None
    # The words of the resume that state it. Facts the owner adds have none.
    quote: str | None = Field(default=None, max_length=600)
    source: Literal["resume", "you"]


def unique_ids(facts: list[Fact]) -> list[Fact]:
    if len({fact.fact_id for fact in facts}) != len(facts):
        raise ValueError("two facts have the same id")
    return facts


class ProfileFacts(BaseModel):
    """What approving a proposal, or saving an edit, sets."""

    model_config = ConfigDict(extra="forbid")

    facts: list[Fact] = Field(max_length=MAX_FACTS)
    source_file_id: uuid.UUID | None = None

    _unique = field_validator("facts")(unique_ids)


class SaveProfile(ProfileFacts):
    # The profile version the edit was based on.
    version: int = Field(ge=0)


class StartParse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: uuid.UUID
    # What the owner confirmed should be hidden from AI.
    hide: Identity


class Version(BaseModel):
    id: uuid.UUID
    version_no: int
    in_use: bool
    approved_at: datetime | None
    facts: list[Fact]
    source_file_id: uuid.UUID | None


class Summary(BaseModel):
    experience_years: str | None
    latest_role: str | None
    skills: list[str]


class Suggestion(BaseModel):
    """Facts waiting for the owner's approval (a proposal)."""

    proposal_id: uuid.UUID
    facts: list[Fact]
    source_file_id: uuid.UUID | None
    # Facts the AI listed whose words were not in the resume.
    dropped: int
    created_at: datetime


class Reading(BaseModel):
    """The latest attempt to read a resume."""

    job_id: uuid.UUID
    file_id: uuid.UUID
    state: Literal["queued", "running", "done", "failed"]
    # Why it is waiting or failed, in words to show.
    problem: str | None
    code: str | None


class Profile(BaseModel):
    # The number to send with the next change.
    version: int
    approved: Version | None
    summary: Summary | None
    suggestion: Suggestion | None
    reading: Reading | None


class Versions(BaseModel):
    items: list[Version]


class Saved(BaseModel):
    profile: Profile
    # Undo with POST /api/events/{event_id}/undo. null when nothing changed.
    event_id: uuid.UUID | None
