"""The one configuration module. Every setting comes from environment variables (or api/.env).

Error messages name the variable that is wrong but never repeat its value, because the value
may be a password.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
EXAMPLE_FILE = "api/.env.example"

DATABASE_PREFIX = "postgresql+psycopg://"
REDIS_PREFIXES = ("redis://", "rediss://")


class ConfigError(Exception):
    """Raised when settings are missing or invalid. The message is safe to print."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # An empty value counts as missing.
        env_ignore_empty=True,
        extra="ignore",
    )

    app_env: Literal["local", "test", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: SecretStr
    redis_url: SecretStr

    # Used only by the automated tests.
    test_database_url: SecretStr | None = None
    test_redis_url: SecretStr | None = None

    @field_validator("database_url", "test_database_url")
    @classmethod
    def check_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().startswith(DATABASE_PREFIX):
            raise ValueError(f"must start with {DATABASE_PREFIX}")
        return value

    @field_validator("redis_url", "test_redis_url")
    @classmethod
    def check_redis_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().startswith(REDIS_PREFIXES):
            raise ValueError("must start with redis:// or rediss://")
        return value


def describe_errors(error: ValidationError) -> str:
    """Turn a validation error into plain lines that name variables and never show values."""
    lines = []
    for item in error.errors(include_input=False, include_url=False):
        name = str(item["loc"][0]).upper() if item["loc"] else "SETTINGS"
        if item["type"] == "missing":
            lines.append(f"  - {name} is missing")
        else:
            lines.append(f"  - {name} is invalid: {item['msg'].removeprefix('Value error, ')}")
    return "\n".join(lines)


def load_settings(env_file: Path | None = ENV_FILE) -> Settings:
    try:
        return Settings(_env_file=env_file)
    except ValidationError as error:
        raise ConfigError(
            "NxtRole cannot start because some settings are wrong:\n"
            f"{describe_errors(error)}\n"
            f"See {EXAMPLE_FILE} for the full list, then fill in api/.env "
            "(or run scripts/new-local-env.ps1 for local development)."
        ) from None


@lru_cache
def get_settings() -> Settings:
    return load_settings()
