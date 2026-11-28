import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.core.errors import AppError
from app.core.idempotency import Answer, IdempotencyKey, run_once
from app.db.session import create_engine, create_session_factory, set_current_user
from tests.integration.factories import one_row_in_every_table, owner_session


class Work:
    """Counts how often the protected action really runs."""

    def __init__(self, fail: bool = False) -> None:
        self.runs = 0
        self.fail = fail

    async def __call__(self) -> tuple[int, dict[str, Any]]:
        self.runs += 1
        await asyncio.sleep(0.05)
        if self.fail:
            raise RuntimeError("the work failed")
        return 201, {"run": self.runs}


@pytest.fixture
async def sessions(test_settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(test_settings.database_url.get_secret_value())
    yield create_session_factory(engine)
    await engine.dispose()


@pytest.fixture
async def user_id(test_settings: Settings) -> uuid.UUID:
    return await one_row_in_every_table(test_settings, "first@example.com")


async def send(
    sessions: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    work: Work,
    body: dict[str, Any],
    key: str = "request-key-1",
) -> Answer:
    async with sessions.begin() as session:
        await set_current_user(session, user_id)
        return await run_once(session, user_id, key, body, work)


async def test_idempotency_key_replays_response(
    sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> None:
    work = Work()

    first = await send(sessions, user_id, work, {"company": "a"})
    second = await send(sessions, user_id, work, {"company": "a"})

    assert work.runs == 1
    assert (first.status_code, first.body, first.replayed) == (201, {"run": 1}, False)
    assert (second.status_code, second.body, second.replayed) == (201, {"run": 1}, True)


async def test_same_key_with_a_different_body_is_a_conflict(
    sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> None:
    work = Work()
    await send(sessions, user_id, work, {"company": "a"})

    with pytest.raises(AppError) as error:
        await send(sessions, user_id, work, {"company": "b"})

    assert error.value.code == "idempotency_conflict"
    assert work.runs == 1


async def test_two_requests_at_the_same_moment_do_the_work_once(
    sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> None:
    work = Work()

    answers = await asyncio.gather(
        *(send(sessions, user_id, work, {"company": "a"}) for _ in range(5))
    )

    assert work.runs == 1
    assert [answer.body for answer in answers] == [{"run": 1}] * 5


async def test_failed_work_keeps_no_key_so_it_can_be_retried(
    sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> None:
    with pytest.raises(RuntimeError):
        await send(sessions, user_id, Work(fail=True), {"company": "a"})
    work = Work()

    answer = await send(sessions, user_id, work, {"company": "a"})

    assert (work.runs, answer.replayed) == (1, False)


async def test_a_key_expires_after_a_day(
    test_settings: Settings,
    sessions: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
) -> None:
    work = Work()
    await send(sessions, user_id, work, {"company": "a"})
    async with owner_session(test_settings) as session:
        await session.execute(
            update(IdempotencyKey).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )

    await send(sessions, user_id, work, {"company": "a"})

    assert work.runs == 2


async def test_two_users_may_use_the_same_key(
    test_settings: Settings,
    sessions: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
) -> None:
    other = await one_row_in_every_table(test_settings, "second@example.com")
    work = Work()

    await send(sessions, user_id, work, {"company": "a"})
    answer = await send(sessions, other, work, {"company": "a"})

    assert (work.runs, answer.replayed) == (2, False)
