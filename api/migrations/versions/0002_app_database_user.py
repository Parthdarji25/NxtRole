"""create the limited database user the API connects as

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Created without a password and unable to sign in. On this computer `setup-local`
    # gives it one; in production the owner does (docs/DEPLOYMENT.md). Later migrations
    # grant it the exact rights it needs on each table (D-039).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nxtrole_app') THEN
                CREATE ROLE nxtrole_app NOLOGIN;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    # The user is shared by every database on the server, so it is left in place.
    # Its rights disappear with the tables.
    pass
