"""Reading a resume with AI, as a tracked job (D-038, D-053).

The request only records the job; the slow work runs after the answer is sent. Until the
separate worker of Phase 8, it runs inside the API: if the API restarts meanwhile, the job
shows as interrupted and can be started again. Nothing is lost.
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import State

from app.ai.factory import gateway_for
from app.ai.gateway import ai_not_set_up, privacy_not_confirmed
from app.ai.privacy import Identity
from app.config import Settings
from app.core.errors import AppError
from app.db.session import set_current_user
from app.files import service as files
from app.history import service as history
from app.history.models import Proposal
from app.profile.extract import extract_facts
from app.worker import repository as jobs
from app.worker.models import BackgroundJob

KIND = "profile_extract"
CHANGE = "profile_facts"
AGENT = "agent:profile"
# A job still "running" after this was cut off.
STALE_AFTER = timedelta(minutes=10)
DEFAULT_WAIT_SECONDS = 60

PROBLEMS = {
    "ai_limits_reached": "The free AI limit is used up for now. Nothing is lost: try again later.",
    "ai_unavailable": "The AI service could not be reached. Try again in a while.",
    "ai_bad_answer": "The AI did not give a usable answer. Please try again.",
    "ai_too_large": "This resume is too long for the free AI limit. Use a shorter file.",
    "ai_blocked": "Personal details were still in the text. Add them to the hidden list.",
    "ai_not_set_up": "AI is not set up: the Groq key is missing or was refused.",
    "privacy_not_confirmed": "Confirm Zero Data Retention before AI reads personal text.",
    "no_facts": "No facts could be confirmed in this resume. Check the file and try again.",
    "interrupted": "Reading stopped before it finished. Try again.",
    "replaced": "A newer upload replaced this one.",
    "internal_error": "Something went wrong on our side. Please try again.",
}

log = structlog.get_logger("nxtrole.profile")


def is_stale(job: BackgroundJob) -> bool:
    return (
        job.state == "running"
        and job.locked_at is not None
        and job.locked_at < datetime.now(UTC) - STALE_AFTER
    )


def check_ready(settings: Settings) -> None:
    """Says at once what is missing, before any job is made."""
    if settings.groq_api_key is None:
        raise ai_not_set_up()
    if settings.groq_zdr_confirmed_on is None:
        raise privacy_not_confirmed()


def _finish(job: BackgroundJob, state: str, error: str | None = None) -> None:
    job.state = state
    job.last_error = error
    job.finished_at = datetime.now(UTC)
    job.locked_at = None


async def start(
    db: AsyncSession,
    settings: Settings,
    user_id: uuid.UUID,
    file_id: uuid.UUID,
    hide: Identity,
) -> tuple[BackgroundJob, bool]:
    """Records the job. The flag says whether it still has to be run."""
    check_ready(settings)
    record = await files.get(db, user_id, file_id)
    if record.status != "ready":
        raise AppError("file_not_ready", "Upload the file first.", status_code=409)
    record.hidden_identity = hide.model_dump()

    current = await jobs.active(db, user_id, KIND)
    if current is not None:
        if current.state == "running" and not is_stale(current):
            # A second tap while it is working: the same job (E-45).
            return current, False
        _finish(current, "failed", "interrupted" if current.state == "running" else "replaced")
        await db.flush()
    job = BackgroundJob(
        user_id=user_id,
        kind=KIND,
        payload={"file_id": str(file_id)},
        state="queued",
        dedupe_key=f"{KIND}:{user_id}",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job, True


async def retry(
    db: AsyncSession, settings: Settings, user_id: uuid.UUID, job_id: uuid.UUID
) -> tuple[BackgroundJob, bool]:
    """ "Try again" for a job that is waiting, failed or was cut off."""
    check_ready(settings)
    job = await jobs.get(db, user_id, job_id, KIND)
    if job is None:
        raise AppError("not_found", "That item does not exist.", status_code=404)
    if job.state == "done" or (job.state == "running" and not is_stale(job)):
        return job, False
    other = await jobs.active(db, user_id, KIND)
    if other is not None and other.id != job.id:
        return other, False
    job.state = "queued"
    job.last_error = None
    job.finished_at = None
    job.locked_at = None
    job.dedupe_key = f"{KIND}:{user_id}"
    await db.flush()
    return job, True


async def run(state: State, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Does the work. Never raises: the outcome is written on the job."""
    claimed = await _claim(state, user_id, job_id)
    if claimed is None:
        return
    file_id, text, hide = claimed
    try:
        result = await extract_facts(gateway_for(state, user_id), text, hide)
    except AppError as error:
        await _record_failure(state, user_id, job_id, error)
        return
    except Exception as error:
        # Only the kind of error: its message could hold resume text.
        log.error("profile_reading_failed", error_type=type(error).__name__)
        await _record_failure(
            state, user_id, job_id, AppError("internal_error", PROBLEMS["internal_error"])
        )
        return

    async with state.sessions.begin() as db:
        await set_current_user(db, user_id)
        job = await jobs.get(db, user_id, job_id, KIND)
        if job is None or job.state != "running":
            return
        if not result.facts:
            _finish(job, "failed", "no_facts")
            return
        # Only the newest suggestion waits for the owner.
        await db.execute(
            update(Proposal)
            .where(
                Proposal.user_id == user_id,
                Proposal.kind == CHANGE,
                Proposal.status == "pending",
            )
            .values(status="expired")
        )
        proposal = await history.propose(
            db,
            user_id,
            CHANGE,
            user_id,
            {
                "facts": [fact.model_dump() for fact in result.facts],
                "source_file_id": str(file_id),
            },
            created_by=AGENT,
        )
        job.result = {
            "proposal_id": str(proposal.id),
            "facts": len(result.facts),
            "dropped": result.dropped,
            "model": result.model,
            "prompt": result.prompt,
        }
        _finish(job, "done")
    log.info("profile_read", facts=len(result.facts), dropped=result.dropped)


async def _claim(
    state: State, user_id: uuid.UUID, job_id: uuid.UUID
) -> tuple[uuid.UUID, str, Identity] | None:
    async with state.sessions.begin() as db:
        await set_current_user(db, user_id)
        job = await jobs.get(db, user_id, job_id, KIND)
        if job is None or job.state != "queued":
            return None
        file_id = uuid.UUID(job.payload["file_id"])
        try:
            record = await files.get(db, user_id, file_id)
        except AppError:
            _finish(job, "failed", "replaced")
            return None
        if record.text_content is None or record.hidden_identity is None:
            _finish(job, "failed", "replaced")
            return None
        job.state = "running"
        job.attempts += 1
        job.locked_by = "api"
        job.locked_at = datetime.now(UTC)
        return file_id, record.text_content, Identity.model_validate(record.hidden_identity)


async def _record_failure(
    state: State, user_id: uuid.UUID, job_id: uuid.UUID, error: AppError
) -> None:
    async with state.sessions.begin() as db:
        await set_current_user(db, user_id)
        statement = select(BackgroundJob).where(
            BackgroundJob.user_id == user_id, BackgroundJob.id == job_id
        )
        job = (await db.scalars(statement.with_for_update())).one_or_none()
        if job is None or job.state != "running":
            return
        if error.code == "ai_limits_reached":
            # It waits, and can be tried again: nothing is lost (E-06).
            wait = int(error.extra.get("retry_after_seconds", DEFAULT_WAIT_SECONDS))
            job.state = "queued"
            job.last_error = error.code
            job.locked_at = None
            job.run_after = datetime.now(UTC) + timedelta(seconds=wait)
        else:
            _finish(job, "failed", error.code)
