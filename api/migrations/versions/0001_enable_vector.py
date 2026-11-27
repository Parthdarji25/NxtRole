"""enable the vector extension (pgvector)

Revision ID: 0001
Revises:
Create Date: 2026-11-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Lets PostgreSQL store and search "embeddings" (meaning vectors), used from Phase 7.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
