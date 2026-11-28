"""Reading the synthetic resume with Groq's real, recorded answers. No network."""

import json
from collections.abc import AsyncIterator

import pytest
from redis.asyncio import Redis

from app.ai.budget import Budget
from app.ai.cassettes import Replay
from app.ai.gateway import Gateway
from app.ai.usage import Used
from app.config import Settings
from app.core.redis import create_redis
from app.profile.extract import extract_facts, normalise
from tests.files_helpers import RESUME_TEXT
from tests.integration.test_profile import ready
from tests.record_ai import RECORDINGS, recording_settings, synthetic_identity

SAVED = sorted(RECORDINGS.glob("*.json"))
needs_recording = pytest.mark.skipif(
    not SAVED, reason="no recorded answer yet: uv run python -m tests.record_ai"
)


@pytest.fixture
async def redis(test_settings: Settings) -> AsyncIterator[Redis]:
    client = create_redis(test_settings.redis_url.get_secret_value())
    yield client
    await client.aclose()


@needs_recording
async def test_the_recorded_answer_gives_checked_facts(
    redis: Redis, test_settings: Settings
) -> None:
    settings = recording_settings(ready(test_settings))

    async def no_usage(_model: str, _used: Used) -> None:
        return None

    gateway = Gateway(Replay(RECORDINGS), Budget(redis, settings), settings, no_usage)

    result = await extract_facts(gateway, RESUME_TEXT, synthetic_identity())

    kinds = {fact.kind for fact in result.facts}
    values = {fact.value for fact in result.facts}
    assert {"role", "skill", "achievement", "education"} <= kinds
    assert {"React", "TypeScript"} <= values
    assert "Frontend Developer" in values
    source = normalise(RESUME_TEXT)
    for fact in result.facts:
        assert fact.quote is not None and normalise(fact.quote) in source, fact.value


@needs_recording
def test_recordings_hold_no_identity() -> None:
    identity = synthetic_identity()
    private = [identity.name, *identity.name.split()]
    private += identity.emails + identity.links + identity.addresses
    private += ["98765", "43210", "12 March 1998"]
    for path in SAVED:
        saved = json.loads(path.read_text(encoding="utf-8"))
        text = (saved["request"]["user"] + saved["reply"]["content"]).casefold()
        for value in private:
            assert value.casefold() not in text, f"{path.name}: {value}"
