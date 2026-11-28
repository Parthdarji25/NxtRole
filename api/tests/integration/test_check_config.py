from pathlib import Path

import pytest

from app.cli import check_config
from app.config import Settings


def write_env(tmp_path: Path, settings: Settings, database_url: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={database_url}\n"
        f"MIGRATION_DATABASE_URL={settings.require_migration_database_url()}\n"
        f"REDIS_URL={settings.redis_url.get_secret_value()}\n"
        f"JWT_SECRET={settings.require_jwt_secret()}\n",
        encoding="utf-8",
    )
    return env_file


@pytest.mark.usefixtures("no_environment")
async def test_check_config_passes_with_services_running(
    tmp_path: Path, test_settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    database_url = test_settings.database_url.get_secret_value()

    exit_code = await check_config(write_env(tmp_path, test_settings, database_url))

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "[ OK ] database: PostgreSQL" in output
    assert "pgvector" in output
    assert "[ OK ] redis" in output
    assert "[ OK ] database user: limited" in output
    assert database_url not in output
    assert test_settings.require_jwt_secret() not in output


@pytest.mark.usefixtures("no_environment")
async def test_check_config_rejects_the_database_owner_as_the_app_user(
    tmp_path: Path, test_settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    owner_url = test_settings.require_migration_database_url()

    exit_code = await check_config(write_env(tmp_path, test_settings, owner_url))

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] database user" in output
    assert "setup-local" in output
    assert owner_url not in output
