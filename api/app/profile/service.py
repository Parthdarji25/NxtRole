"""The profile as the screens see it."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.history.models import Proposal
from app.profile import reading, repository
from app.profile.models import ProfileVersion
from app.profile.schemas import Fact, Profile, Reading, Suggestion, Summary, Version
from app.worker import repository as jobs
from app.worker.models import BackgroundJob


def as_version(row: ProfileVersion) -> Version:
    return Version(
        id=row.id,
        version_no=row.version_no,
        in_use=row.status == "approved",
        approved_at=row.approved_at,
        facts=[Fact.model_validate(fact) for fact in row.facts],
        source_file_id=row.source_file_id,
    )


def summarise(facts: list[Fact]) -> Summary:
    """The three things the setup screen shows: experience, latest role, skills."""
    roles = [fact for fact in facts if fact.kind == "role"]
    current = [
        role
        for role in roles
        if any(word in (role.dates or "").casefold() for word in ("present", "current"))
    ]
    latest = next(iter(current or roles), None)
    years = next((fact.value for fact in facts if fact.kind == "experience_years"), None)
    return Summary(
        experience_years=years,
        latest_role=latest.value if latest else None,
        skills=[fact.value for fact in facts if fact.kind == "skill"],
    )


def as_reading(job: BackgroundJob) -> Reading:
    state = job.state if job.state != "dead" else "failed"
    code = job.last_error
    if reading.is_stale(job):
        state, code = "failed", "interrupted"
    return Reading(
        job_id=job.id,
        file_id=uuid.UUID(job.payload["file_id"]),
        state=state,
        code=code,
        problem=reading.PROBLEMS.get(code) if code else None,
    )


async def suggestion(db: AsyncSession, user_id: uuid.UUID) -> Suggestion | None:
    statement = (
        select(Proposal)
        .where(
            Proposal.user_id == user_id,
            Proposal.kind == reading.CHANGE,
            Proposal.status == "pending",
        )
        .order_by(Proposal.created_at.desc())
        .limit(1)
    )
    proposal = (await db.scalars(statement)).one_or_none()
    if proposal is None:
        return None
    job = await jobs.latest(db, user_id, reading.KIND)
    result = (job.result or {}) if job else {}
    dropped = result.get("dropped", 0) if result.get("proposal_id") == str(proposal.id) else 0
    return Suggestion(
        proposal_id=proposal.id,
        facts=[Fact.model_validate(fact) for fact in proposal.payload["facts"]],
        source_file_id=proposal.payload.get("source_file_id"),
        dropped=dropped,
        created_at=proposal.created_at,
    )


async def profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    row = await repository.approved(db, user_id)
    approved = as_version(row) if row else None
    job = await jobs.latest(db, user_id, reading.KIND)
    return Profile(
        version=await repository.latest_number(db, user_id),
        approved=approved,
        summary=summarise(approved.facts) if approved else None,
        suggestion=await suggestion(db, user_id),
        reading=as_reading(job) if job else None,
    )
