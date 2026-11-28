"""The career profile under /api/profile.

Suggested facts are approved or rejected with the shared proposal addresses
(POST /api/proposals/{id}/approve and /reject).
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from app.core.deps import CurrentUser
from app.history import service as history
from app.history.snapshot import not_found
from app.profile import reading, repository, service
from app.profile.schemas import (
    Profile,
    Reading,
    Saved,
    SaveProfile,
    StartParse,
    Versions,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=Profile)
async def read(current: CurrentUser) -> Profile:
    return await service.profile(current.db, current.user.id)


@router.put("", response_model=Saved)
async def save(body: SaveProfile, current: CurrentUser) -> Saved:
    """The owner's own edit of the approved facts: a new version, with undo."""
    event = await history.apply_change(
        current.db,
        current.user.id,
        reading.CHANGE,
        current.user.id,
        body.model_dump(mode="json", exclude={"version"}),
        expected_version=body.version,
    )
    profile = await service.profile(current.db, current.user.id)
    return Saved(profile=profile, event_id=event.id if event else None)


@router.get("/versions", response_model=Versions)
async def versions(current: CurrentUser) -> Versions:
    rows = await repository.versions(current.db, current.user.id)
    # Versions that only record "no profile" are not offered.
    return Versions(items=[service.as_version(row) for row in rows if row.approved_at])


@router.post("/versions/{version_id}/restore", response_model=Saved)
async def restore(version_id: uuid.UUID, current: CurrentUser) -> Saved:
    """Uses an older version again, as a new version."""
    old = await repository.get(current.db, current.user.id, version_id)
    if old is None or old.approved_at is None:
        raise not_found()
    source = old.source_file_id
    event = await history.apply_change(
        current.db,
        current.user.id,
        reading.CHANGE,
        current.user.id,
        {"facts": old.facts, "source_file_id": str(source) if source else None},
        expected_version=None,
    )
    profile = await service.profile(current.db, current.user.id)
    return Saved(profile=profile, event_id=event.id if event else None)


@router.post("/parse", response_model=Reading, status_code=202)
async def parse(
    body: StartParse, request: Request, tasks: BackgroundTasks, current: CurrentUser
) -> Reading:
    """Asks AI to read an uploaded resume. The answer arrives later."""
    state = request.app.state
    job, to_run = await reading.start(
        current.db, state.settings, current.user.id, body.file_id, body.hide
    )
    if to_run:
        # Runs after the answer is sent, when the job has been saved.
        tasks.add_task(reading.run, state, current.user.id, job.id)
    return service.as_reading(job)


@router.post("/parse/{job_id}/retry", response_model=Reading, status_code=202)
async def retry(
    job_id: uuid.UUID, request: Request, tasks: BackgroundTasks, current: CurrentUser
) -> Reading:
    state = request.app.state
    job, to_run = await reading.retry(current.db, state.settings, current.user.id, job_id)
    if to_run:
        tasks.add_task(reading.run, state, current.user.id, job.id)
    return service.as_reading(job)
