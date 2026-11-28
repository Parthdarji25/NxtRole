"""users, sessions, repeated-request keys, proposals and history, with row-level security

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-27
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Whose rows the current transaction may see. Empty or unset means nobody's.
CURRENT_USER = "NULLIF(current_setting('app.user_id', true), '')::uuid"

# Table -> (column that names the owner, what the app's database user may do).
# History is append-only: the app may add rows and mark one as undone, nothing else.
RIGHTS = {
    "users": ("id", "SELECT, UPDATE"),
    "refresh_tokens": ("user_id", "SELECT, INSERT, UPDATE, DELETE"),
    "idempotency_keys": ("user_id", "SELECT, INSERT, UPDATE, DELETE"),
    "proposals": ("user_id", "SELECT, INSERT, UPDATE"),
    "events": ("user_id", "SELECT, INSERT, UPDATE (undone_by)"),
}

# Before sign-in nobody is known yet, so row-level security would hide everything. These two
# functions run with the owner's rights and answer one narrow question each: only an id.
LOOKUPS = {
    "auth_user_id_for_email(p_email text)": (
        "SELECT id FROM public.users WHERE email = p_email::public.citext"
    ),
    "auth_user_id_for_token(p_hash text)": (
        "SELECT user_id FROM public.refresh_tokens WHERE token_hash = p_hash"
    ),
}


def id_column() -> sa.Column[Any]:
    return sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True)


def time_column(name: str, *, default_now: bool = False, nullable: bool = False) -> sa.Column[Any]:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.func.now() if default_now else None,
        nullable=nullable,
    )


def user_column() -> sa.Column[Any]:
    return sa.Column(
        "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def version_column() -> sa.Column[Any]:
    return sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False)


def upgrade() -> None:
    # Text that compares without regard to capitals, for email addresses.
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        id_column(),
        time_column("created_at", default_now=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("recovery_code_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failed_logins", sa.Integer(), server_default=sa.text("0"), nullable=False),
        time_column("last_failed_at", nullable=True),
        time_column("locked_until", nullable=True),
        version_column(),
        time_column("updated_at", default_now=True),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 80", name="display_name_length"
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "refresh_tokens",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        time_column("expires_at"),
        time_column("used_at", nullable=True),
        time_column("revoked_at", nullable=True),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_hint", sa.Text()),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index(
        "ix_refresh_tokens_user_id_family_id", "refresh_tokens", ["user_id", "family_id"]
    )
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "idempotency_keys",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        time_column("expires_at"),
        sa.UniqueConstraint("user_id", "key", name="uq_idempotency_keys_user_id_key"),
    )

    op.create_table(
        "proposals",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        version_column(),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Uuid()),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("base_version", sa.Integer()),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Uuid()),
        time_column("decided_at", nullable=True),
        time_column("updated_at", default_now=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'applied', 'failed')",
            name="status",
        ),
    )
    op.create_index("ix_proposals_user_id_status", "proposals", ["user_id", "status"])

    op.create_table(
        "events",
        id_column(),
        user_column(),
        time_column("occurred_at", default_now=True),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("before", postgresql.JSONB()),
        sa.Column("after", postgresql.JSONB()),
        sa.Column("proposal_id", sa.Uuid(), sa.ForeignKey("proposals.id")),
        sa.Column("undone_by", sa.Uuid(), sa.ForeignKey("events.id")),
        sa.Column("undo_of", sa.Uuid(), sa.ForeignKey("events.id")),
        sa.Column("note", sa.Text()),
    )
    op.create_index(
        "ix_events_user_id_occurred_at", "events", ["user_id", sa.text("occurred_at DESC")]
    )
    op.create_index("ix_events_target_type_target_id", "events", ["target_type", "target_id"])

    for table, (owner_column, rights) in RIGHTS.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_own_rows ON {table} "
            f"USING ({owner_column} = {CURRENT_USER}) "
            f"WITH CHECK ({owner_column} = {CURRENT_USER})"
        )
        op.execute(f"GRANT {rights} ON {table} TO nxtrole_app")

    for signature, query in LOOKUPS.items():
        op.execute(
            f"CREATE FUNCTION {signature} RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER "
            f"SET search_path = pg_catalog, public, pg_temp AS $$ {query} $$"
        )
        name = signature.split("(")[0]
        op.execute(f"REVOKE ALL ON FUNCTION {name}(text) FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {name}(text) TO nxtrole_app")


def downgrade() -> None:
    for signature in LOOKUPS:
        op.execute(f"DROP FUNCTION IF EXISTS {signature.split('(')[0]}(text)")
    # In reverse order, because later tables point at earlier ones.
    for table in reversed(list(RIGHTS)):
        op.drop_table(table)
    op.execute("DROP EXTENSION IF EXISTS citext")
