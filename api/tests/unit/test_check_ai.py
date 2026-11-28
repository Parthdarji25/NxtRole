from datetime import date

import pytest
from pydantic import SecretStr

from app.ai import check
from app.ai.transport import NotConfigured
from app.config import Settings
from tests.conftest import make_settings, unreachable_database_url, unreachable_redis_url

KEY = "test-key-that-opens-nothing"


def settings(**values: object) -> Settings:
    return make_settings(unreachable_database_url(), unreachable_redis_url(), **values)


def provider(monkeypatch: pytest.MonkeyPatch, models: list[str] | Exception) -> None:
    class Fake:
        def __init__(self, key: str) -> None:
            assert key == KEY

        async def list_models(self) -> list[str]:
            if isinstance(models, Exception):
                raise models
            return models

        async def close(self) -> None:
            return None

    monkeypatch.setattr(check, "GroqTransport", Fake)


async def run(config: Settings) -> tuple[int, str]:
    said: list[str] = []
    code = await check.check_ai(config, said.append)
    return code, "\n".join(said)


async def test_a_missing_key_says_where_to_put_it() -> None:
    code, output = await run(settings())

    assert code == 1
    assert "GROQ_API_KEY=your-key" in output


async def test_all_good(monkeypatch: pytest.MonkeyPatch) -> None:
    provider(monkeypatch, ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"])

    code, output = await run(
        settings(groq_api_key=SecretStr(KEY), groq_zdr_confirmed_on=date(2026, 11, 28))
    )

    assert code == 0, output
    assert "confirmed it on 2026-11-28" in output
    assert KEY not in output


async def test_a_missing_model_and_confirmation_are_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider(monkeypatch, ["openai/gpt-oss-20b"])

    code, output = await run(settings(groq_api_key=SecretStr(KEY)))

    assert code == 1
    assert "openai/gpt-oss-120b is not offered" in output
    assert "GROQ_ZDR_CONFIRMED_ON" in output


async def test_a_refused_key_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    provider(monkeypatch, NotConfigured("the provider refused the key"))

    code, output = await run(settings(groq_api_key=SecretStr(KEY)))

    assert code == 1
    assert "refused the key" in output
    assert KEY not in output
