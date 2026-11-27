from pathlib import Path

import pytest

from app.config import ConfigError, load_settings

pytestmark = pytest.mark.usefixtures("no_environment")

DATABASE = "postgresql+psycopg://user:hidden-value@127.0.0.1:5432/nxtrole"
REDIS = "redis://127.0.0.1:6379/0"


def write_env(tmp_path: Path, *lines: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_file


def test_config_missing_variables_are_all_named(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as error:
        load_settings(write_env(tmp_path))

    message = str(error.value)
    assert "DATABASE_URL is missing" in message
    assert "REDIS_URL is missing" in message
    assert "api/.env.example" in message


def test_config_empty_value_counts_as_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as error:
        load_settings(write_env(tmp_path, "DATABASE_URL=", f"REDIS_URL={REDIS}"))

    assert "DATABASE_URL is missing" in str(error.value)
    assert "REDIS_URL" not in str(error.value).split("See ")[0]


def test_config_invalid_value_names_variable_without_showing_it(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path, "DATABASE_URL=mysql://user:hidden-value@db/app", f"REDIS_URL={REDIS}"
    )

    with pytest.raises(ConfigError) as error:
        load_settings(env_file)

    message = str(error.value)
    assert "DATABASE_URL is invalid" in message
    assert "hidden-value" not in message
    # The original validation error (which holds the value) is not chained to the message.
    assert error.value.__suppress_context__ is True


def test_config_invalid_environment_name_is_rejected(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path, "APP_ENV=staging", f"DATABASE_URL={DATABASE}", f"REDIS_URL={REDIS}"
    )

    with pytest.raises(ConfigError, match="APP_ENV is invalid"):
        load_settings(env_file)


def test_config_valid_file_loads_and_hides_secrets(tmp_path: Path) -> None:
    settings = load_settings(write_env(tmp_path, f"DATABASE_URL={DATABASE}", f"REDIS_URL={REDIS}"))

    assert settings.app_env == "local"
    assert settings.database_url.get_secret_value() == DATABASE
    assert "hidden-value" not in repr(settings)


def test_config_environment_variable_wins_over_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    settings = load_settings(
        write_env(tmp_path, "LOG_LEVEL=DEBUG", f"DATABASE_URL={DATABASE}", f"REDIS_URL={REDIS}")
    )

    assert settings.log_level == "ERROR"
