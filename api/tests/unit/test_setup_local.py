from pathlib import Path

import pytest

from app.config import ConfigError, load_settings
from app.setup_local import setup_local, update_env_file

APP_URL = "postgresql+psycopg://owner:hidden-value@127.0.0.1:5432/nxtrole"


def write(tmp_path: Path, *lines: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_file


def test_update_env_file_replaces_and_adds_without_losing_lines(tmp_path: Path) -> None:
    env_file = write(tmp_path, "# my note", "A=old", "", "B=stays")

    update_env_file(env_file, {"A": "new", "C": "added"})

    assert env_file.read_text(encoding="utf-8").splitlines() == [
        "# my note",
        "A=new",
        "",
        "B=stays",
        "C=added",
    ]


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        ([], "DATABASE_URL is missing"),
        (["APP_ENV=production", f"DATABASE_URL={APP_URL}"], "production"),
        (
            ["DATABASE_URL=postgresql+psycopg://owner:hidden-value@db.example:5432/nxtrole"],
            "on this computer",
        ),
        (
            ["DATABASE_URL=postgresql+psycopg://nxtrole_app:hidden-value@127.0.0.1/nxtrole"],
            "database owner",
        ),
    ],
)
def test_setup_local_refuses_unsafe_situations(
    tmp_path: Path, lines: list[str], message: str
) -> None:
    env_file = write(tmp_path, *lines)
    before = env_file.read_bytes()

    with pytest.raises(ConfigError, match=message) as error:
        setup_local(env_file)

    assert "hidden-value" not in str(error.value)
    assert env_file.read_bytes() == before


def test_setup_local_explains_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"new-local-env\.ps1"):
        setup_local(tmp_path / ".env")


@pytest.mark.usefixtures("no_environment")
def test_a_short_signing_secret_is_rejected_without_showing_it(tmp_path: Path) -> None:
    env_file = write(
        tmp_path,
        f"DATABASE_URL={APP_URL}",
        "REDIS_URL=redis://127.0.0.1:6379/0",
        "JWT_SECRET=too-short-value",
    )

    with pytest.raises(ConfigError, match="JWT_SECRET is invalid") as error:
        load_settings(env_file)

    assert "too-short-value" not in str(error.value)


@pytest.mark.usefixtures("no_environment")
def test_missing_sign_in_settings_say_what_to_run(tmp_path: Path) -> None:
    settings = load_settings(
        write(tmp_path, f"DATABASE_URL={APP_URL}", "REDIS_URL=redis://127.0.0.1:6379/0")
    )

    with pytest.raises(ConfigError, match="setup-local"):
        settings.require_jwt_secret()
    with pytest.raises(ConfigError, match="setup-local"):
        settings.require_migration_database_url()
