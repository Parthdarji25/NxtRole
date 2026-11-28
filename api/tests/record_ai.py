"""Records Groq's real answers for the tests:  uv run python -m tests.record_ai

It sends ONLY the synthetic resume in tests/fixtures (an invented person), with identity
removed, using the key in api/.env. It uses a little of the free daily allowance. Never
point it at a real resume.
"""

import asyncio
import sys

from app.ai.budget import Budget
from app.ai.cassettes import Recorder
from app.ai.gateway import Gateway
from app.ai.privacy import Identity, detect
from app.ai.transport import GroqTransport
from app.ai.usage import Used
from app.config import ConfigError, Settings, load_settings
from app.core.errors import AppError
from app.core.loop import new_event_loop
from app.core.redis import create_redis
from app.profile.extract import extract_facts
from tests.files_helpers import FIXTURES, RESUME_TEXT

RECORDINGS = FIXTURES / "ai"


def synthetic_identity() -> Identity:
    found = detect(RESUME_TEXT)
    assert found.name is not None
    return Identity(**found.model_dump())


def recording_settings(settings: Settings) -> Settings:
    """The default models and limits, so that tests make exactly the same requests."""
    defaults = {
        name: Settings.model_fields[name].default
        for name in (
            "ai_main_model",
            "ai_small_model",
            "ai_judge_model",
            "ai_tokens_per_minute",
        )
    }
    return settings.model_copy(update=defaults)


async def record() -> int:
    try:
        settings = recording_settings(load_settings())
    except ConfigError as error:
        print(error)
        return 1
    if settings.groq_api_key is None or settings.groq_zdr_confirmed_on is None:
        print("Fill in GROQ_API_KEY and GROQ_ZDR_CONFIRMED_ON in api/.env first.")
        return 1
    transport = GroqTransport(settings.groq_api_key.get_secret_value())
    recorder = Recorder(transport, RECORDINGS)
    redis = create_redis(settings.redis_url.get_secret_value())

    async def no_usage(_model: str, _used: Used) -> None:
        return None

    gateway = Gateway(recorder, Budget(redis, settings), settings, no_usage)
    try:
        result = await extract_facts(gateway, RESUME_TEXT, synthetic_identity())
    except AppError as error:
        print(f"Not recorded: {error.code}. {error.message}")
        return 1
    finally:
        await transport.close()
        await redis.aclose()
    print(f"Recorded {len(recorder.written)} answer(s) from {result.model}:")
    for path in recorder.written:
        print(f"  {path.name}")
    print(f"Facts kept: {len(result.facts)}. Left out by the quote check: {result.dropped}.")
    for fact in result.facts:
        print(f"  {fact.kind:17} {fact.value}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(record(), loop_factory=new_event_loop))
