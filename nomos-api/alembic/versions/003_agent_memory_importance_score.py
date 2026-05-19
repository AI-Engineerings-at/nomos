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

    server_default keeps any pre-existing rows valid and matches the
    model's Python-side default=1.0.
    """
    with op.batch_alter_table("agent_memory") as batch_op:
        batch_op.add_column(
            sa.Column(
                "importance_score",
                sa.Float(),
                nullable=False,
                server_default="1.0",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_memory") as batch_op:
        batch_op.drop_column("importance_score")
