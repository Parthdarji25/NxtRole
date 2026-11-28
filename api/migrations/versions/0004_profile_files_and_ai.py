"""files, background jobs, profile versions, preferences, rules and AI usage

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-28
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT_USER = "NULLIF(current_setting('app.user_id', true), '')::uuid"

# Table -> what the app's database user may do (the owner column is always user_id).
RIGHTS = {
    "files": "SELECT, INSERT, UPDATE, DELETE",
    "background_jobs": "SELECT, INSERT, UPDATE, DELETE",
    "profile_versions": "SELECT, INSERT, UPDATE",
    "search_preferences": "SELECT, INSERT, UPDATE",
    "rules": "SELECT, INSERT, UPDATE, DELETE",
    "ai_usage": "SELECT, INSERT, UPDATE",
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


def user_column(*, primary_key: bool = False, nullable: bool = False) -> sa.Column[Any]:
    return sa.Column(
        "user_id",
        sa.Uuid(),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=primary_key,
        nullable=nullable,
    )


def count_column(name: str, *, small: bool = False, default: int = 0) -> sa.Column[Any]:
    return sa.Column(
        name,
        sa.SmallInteger() if small else sa.Integer(),
        server_default=sa.text(str(default)),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "files",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.Text()),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("text_content", sa.Text()),
        sa.Column("truncated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("hidden_identity", postgresql.JSONB()),
        time_column("expires_at", nullable=True),
        sa.CheckConstraint("status IN ('pending', 'ready', 'rejected', 'deleted')", name="status"),
    )
    op.create_index("ix_files_user_id_kind", "files", ["user_id", "kind"])

    op.create_table(
        "background_jobs",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(nullable=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column(
            "payload", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("result", postgresql.JSONB()),
        sa.Column("state", sa.Text(), server_default="queued", nullable=False),
        time_column("run_after", default_now=True),
        count_column("attempts", small=True),
        count_column("max_attempts", small=True, default=5),
        sa.Column("locked_by", sa.Text()),
        time_column("locked_at", nullable=True),
        sa.Column("dedupe_key", sa.Text()),
        sa.Column("last_error", sa.Text()),
        time_column("finished_at", nullable=True),
        sa.CheckConstraint(
            "state IN ('queued', 'running', 'done', 'failed', 'dead')", name="state"
        ),
    )
    op.create_index("ix_background_jobs_state_run_after", "background_jobs", ["state", "run_after"])
    op.create_index(
        "uq_background_jobs_active_dedupe_key",
        "background_jobs",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running')"),
    )

    op.create_table(
        "profile_versions",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("facts", postgresql.JSONB(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), sa.ForeignKey("files.id", ondelete="SET NULL")),
        time_column("approved_at", nullable=True),
        sa.CheckConstraint("status IN ('approved', 'superseded')", name="status"),
        sa.UniqueConstraint("user_id", "version_no", name="uq_profile_versions_user_id_version_no"),
    )
    op.create_index(
        "uq_profile_versions_user_id_approved",
        "profile_versions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )

    op.create_table(
        "search_preferences",
        user_column(primary_key=True),
        sa.Column(
            "titles",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "places",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("experience_min", sa.SmallInteger()),
        sa.Column("experience_max", sa.SmallInteger()),
        sa.Column("notice_days", sa.SmallInteger()),
        sa.Column("expected_ctc_inr", sa.BigInteger()),
        count_column("onboarding_step", small=True, default=1),
        count_column("version", default=1),
        time_column("updated_at", default_now=True),
    )

    op.create_table(
        "rules",
        id_column(),
        time_column("created_at", default_now=True),
        user_column(),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("evidence", postgresql.JSONB()),
        time_column("dismissed_until", nullable=True),
        count_column("hid_count"),
        count_column("version", default=1),
        sa.CheckConstraint("origin IN ('you', 'learned')", name="origin"),
        sa.CheckConstraint("status IN ('active', 'suggested', 'dismissed')", name="status"),
    )
    op.create_index("ix_rules_user_id_status", "rules", ["user_id", "status"])
    op.create_index(
        "uq_rules_user_id_kind_you",
        "rules",
        ["user_id", "kind"],
        unique=True,
        postgresql_where=sa.text("origin = 'you'"),
    )

    op.create_table(
        "ai_usage",
        user_column(primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("provider", sa.Text(), primary_key=True),
        sa.Column("model", sa.Text(), primary_key=True),
        count_column("requests"),
        count_column("tokens_in"),
        count_column("tokens_out"),
        count_column("errors"),
        count_column("rate_limited"),
    )

    for table, rights in RIGHTS.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_own_rows ON {table} "
            f"USING (user_id = {CURRENT_USER}) WITH CHECK (user_id = {CURRENT_USER})"
        )
        op.execute(f"GRANT {rights} ON {table} TO nxtrole_app")


def downgrade() -> None:
    # In reverse order, because later tables point at earlier ones.
    for table in reversed(list(RIGHTS)):
        op.drop_table(table)
