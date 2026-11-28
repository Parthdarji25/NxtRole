"""setup-local against a real database, with a throw-away user name."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import dotenv_values
from psycopg import sql
from sqlalchemy.engine import make_url

from app.config import Settings
from app.setup_local import connect, setup_local

ROLE = "nxtrole_setup_test"


@pytest.fixture
def throw_away_role(test_settings: Settings) -> Iterator[None]:
    yield
    owner = make_url(test_settings.require_migration_database_url())
    with connect(owner) as connection:
        connection.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(ROLE)))


@pytest.mark.usefixtures("throw_away_role")
def test_setup_local_creates_a_limited_user_and_a_secret(
    tmp_path: Path, test_settings: Settings
) -> None:
    owner_url = test_settings.require_migration_database_url()
    env_file = tmp_path / ".env"
    env_file.write_text(f"# keep me\nDATABASE_URL={owner_url}\n", encoding="utf-8")

    done = setup_local(env_file, role=ROLE)

    values = dotenv_values(env_file)
    assert values["MIGRATION_DATABASE_URL"] == owner_url
    assert values["JWT_SECRET"] is not None and len(values["JWT_SECRET"]) >= 32
    app = make_url(str(values["DATABASE_URL"]))
    assert app.username == ROLE
    with connect(app) as connection:
        limits = connection.execute(
            "SELECT rolsuper, rolbypassrls, rolcreaterole FROM pg_roles "
            "WHERE rolname = current_user"
        ).fetchone()
    assert limits == (False, False, False)
    assert env_file.read_text(encoding="utf-8").startswith("# keep me\n")
    # Nothing secret appears in what is printed.
    printed = " ".join(done)
    assert str(app.password) not in printed
    assert values["JWT_SECRET"] not in printed


@pytest.mark.usefixtures("throw_away_role")
def test_setup_local_twice_changes_nothing(tmp_path: Path, test_settings: Settings) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={test_settings.require_migration_database_url()}\n", encoding="utf-8"
    )
    setup_local(env_file, role=ROLE)
    first = env_file.read_bytes()

    done = setup_local(env_file, role=ROLE)

    assert env_file.read_bytes() == first
    assert done == [f"database user '{ROLE}' is ready"]
