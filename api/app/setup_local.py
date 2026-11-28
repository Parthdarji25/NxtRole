"""Prepares api/.env for sign-in on this computer:  uv run python -m app.cli setup-local

It creates a limited database user for the app (so the database itself can keep one person's
rows away from another, D-039) and a secret for signing access tokens. It never prints a
password or a secret. Running it again changes nothing that already works.
"""

import secrets
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from psycopg import sql
from sqlalchemy.engine import URL, make_url

from app.config import MIN_SECRET_LENGTH, ConfigError
from app.db.roles import APP_ROLE

LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
CONNECT_TIMEOUT_SECONDS = 3


def connect(url: URL) -> psycopg.Connection:
    return psycopg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        dbname=url.database,
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        autocommit=True,
    )


def ensure_login_role(owner: URL, role: str, password: str) -> None:
    """Create the app's database user if needed and give it this password."""
    with connect(owner) as connection:
        found = connection.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
        if found is None:
            connection.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
        connection.execute(
            sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )


def update_env_file(path: Path, updates: dict[str, str]) -> None:
    """Replace or add NAME=value lines, keeping every other line as it was."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    remaining = dict(updates)
    for index, line in enumerate(lines):
        name = line.split("=", 1)[0].strip()
        if "=" in line and name in remaining:
            lines[index] = f"{name}={remaining.pop(name)}"
    lines.extend(f"{name}={value}" for name, value in remaining.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def setup_local(env_file: Path, role: str = APP_ROLE) -> list[str]:
    """Returns plain lines saying what changed. Values are never part of them."""
    if not env_file.exists():
        raise ConfigError(
            "api/.env does not exist yet. From the repository root run:  "
            "powershell -ExecutionPolicy Bypass -File scripts/new-local-env.ps1"
        )
    values = {name: value for name, value in dotenv_values(env_file).items() if value}
    if values.get("APP_ENV") == "production":
        raise ConfigError("setup-local is for this computer only. APP_ENV is production.")
    app_value = values.get("DATABASE_URL")
    if app_value is None:
        raise ConfigError("DATABASE_URL is missing from api/.env.")

    # Before the first run DATABASE_URL belongs to the database owner.
    owner_value = values.get("MIGRATION_DATABASE_URL", app_value)
    owner = make_url(owner_value)
    if owner.host not in LOCAL_HOSTS:
        raise ConfigError("setup-local only changes a database on this computer.")
    if owner.username == role:
        raise ConfigError(
            "MIGRATION_DATABASE_URL must use the database owner, not the app's own user."
        )

    app = make_url(app_value)
    password = app.password if app.username == role and app.password else secrets.token_hex(24)
    app = app.set(username=role, password=str(password))
    ensure_login_role(owner, role, str(password))

    updates: dict[str, str] = {}
    done = [f"database user '{role}' is ready"]
    if "MIGRATION_DATABASE_URL" not in values:
        updates["MIGRATION_DATABASE_URL"] = owner_value
        done.append("added MIGRATION_DATABASE_URL (the database owner)")
    new_app_value = app.render_as_string(hide_password=False)
    if new_app_value != app_value:
        updates["DATABASE_URL"] = new_app_value
        done.append("DATABASE_URL now uses the limited app user")
    if len(values.get("JWT_SECRET", "")) < MIN_SECRET_LENGTH:
        updates["JWT_SECRET"] = secrets.token_urlsafe(48)
        done.append("added JWT_SECRET")
    if updates:
        update_env_file(env_file, updates)
    return done
