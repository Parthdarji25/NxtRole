from pathlib import Path

import pytest

from app.cli import check_config, describe_url
from tests.conftest import unreachable_database_url, unreachable_redis_url

pytestmark = pytest.mark.usefixtures("no_environment")


def test_describe_url_never_shows_user_or_password() -> None:
    described = describe_url("postgresql+psycopg://owner:hidden-value@db.example:5432/nxtrole")

    assert described == "db.example:5432/nxtrole"


async def test_check_config_lists_missing_variables(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")

    exit_code = await check_config(env_file)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "DATABASE_URL is missing" in output
    assert "REDIS_URL is missing" in output


async def test_check_config_explains_unreachable_services(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={unreachable_database_url()}\nREDIS_URL={unreachable_redis_url()}\n",
        encoding="utf-8",
    )

    exit_code = await check_config(env_file)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] database" in output
    assert "[FAIL] redis" in output
    assert "wsl docker compose up -d" in output
    assert "not-a-real-password" not in output
