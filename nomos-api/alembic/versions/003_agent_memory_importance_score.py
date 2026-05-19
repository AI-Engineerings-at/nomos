"""Add missing agent_memory.importance_score column.

The AgentMemory model declares `importance_score` (used by the context
pipeline's store_message), but 001_initial_schema never created it.
Unit tests pass because conftest builds the schema via
Base.metadata.create_all (from the model); the real deployment uses
Alembic, so on Postgres every context-pipeline write — i.e. every chat
turn — failed with UndefinedColumnError -> HTTP 500. This closes that
model<->migration drift.

Revision ID: agent_memory_importance_score
Revises: monitoring_tables
Create Date: 2026-05-19 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "agent_memory_importance_score"
down_revision = "monitoring_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add importance_score (NOT NULL, server_default 1.0) to agent_memory.

    Plain ``op.add_column`` (not ``batch_alter_table``): Postgres can ADD
    COLUMN with a server_default in O(1) (PG11+ fast-path for non-volatile
    defaults). ``batch_alter_table`` defaults to copy-and-rename for
    portability, which would rewrite the entire (potentially multi-million
    row) ``agent_memory`` table under lock — gratuitous on a Postgres-only
    deployment. SQLite isn't a production target; test suite uses
    create_all anyway.
    """
    op.add_column(
        "agent_memory",
        sa.Column("importance_score", sa.Float(), nullable=False, server_default="1.0"),
    )


def downgrade() -> None:
    op.drop_column("agent_memory", "importance_score")
