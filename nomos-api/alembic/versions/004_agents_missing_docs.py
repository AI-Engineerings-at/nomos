"""Add agents.missing_docs JSON column for v0.4.0 compliance-matrix cache.

v0.4.0 (P1 / audit C-F2): the previous ``/api/compliance/matrix``
endpoint walked every agent on disk, loaded the manifest, parsed the
YAML, and re-ran ``check_compliance`` per agent — synchronous, O(N) disk
I/O per request. At 200 agents this is hundreds of seek+parse cycles
inside a request handler.

This migration adds a denormalised ``missing_docs`` JSON column on the
``agents`` table. The hire path (POST /api/agents) and the gate path
(POST /api/agents/{id}/gate) write the current value when they finish.
The matrix endpoint then reads agents straight from the DB in one
query and never touches disk.

Schema-only migration: an empty list ``[]`` is the safe default for
existing rows; the matrix endpoint also tolerates ``NULL`` and
re-computes for legacy rows on the next gate run.

Revision ID: agents_missing_docs
Revises: agent_memory_importance_score
Create Date: 2026-05-20 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "agents_missing_docs"
down_revision = "agent_memory_importance_score"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ``missing_docs JSON NOT NULL DEFAULT '[]'`` to ``agents``."""
    op.add_column(
        "agents",
        sa.Column(
            "missing_docs",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "missing_docs")
