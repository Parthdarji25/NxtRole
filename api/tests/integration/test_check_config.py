from pathlib import Path

import pytest

from app.cli import check_config
from app.config import Settings


@pytest.mark.usefixtures("no_environment")
async def test_check_config_passes_with_services_running(
    tmp_path: Path, test_settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    env_file = tmp_path / ".env"
    database_url = test_settings.database_url.get_secret_value()
    redis_url = test_settings.redis_url.get_secret_value()
    env_file.write_text(f"DATABASE_URL={database_url}\nREDIS_URL={redis_url}\n", encoding="utf-8")

    exit_code = await check_config(env_file)

    output = capsys.readouterr().out
    assert exit_code == 0, output
    assert "[ OK ] database: PostgreSQL" in output
    assert "pgvector" in output
    assert "[ OK ] redis" in output
    assert database_url not in output
