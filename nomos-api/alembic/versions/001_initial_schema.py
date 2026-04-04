"""Initial schema — all NomOS tables.

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-31

Tables: agents, audit_log, incidents, users, tasks, approvals,
        config_revisions, agent_memory, workspace_mounts
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- agents ---
    op.create_table(
        "agents",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("role", sa.String(256), nullable=False),
        sa.Column("company", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("risk_class", sa.String(32), nullable=False, server_default="limited"),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("manifest_hash", sa.String(64), nullable=False),
        sa.Column("manifest_data", sa.JSON, nullable=False),
        sa.Column("compliance_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("agents_dir", sa.Text, nullable=False),
        sa.Column("budget_used_eur", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("budget_limit_eur", sa.Float, nullable=False, server_default="50.0"),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- audit_log ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("data", sa.JSON, nullable=True),
        sa.Column("chain_hash", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.String(64), nullable=False),
    )
    op.create_index("ix_audit_log_agent_id", "audit_log", ["agent_id"])
    op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])
    op.create_index("ix_audit_log_agent_sequence", "audit_log", ["agent_id", "sequence"])

    # --- incidents ---
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("incident_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="detected"),
        sa.Column("detected_at", sa.String(64), nullable=False),
        sa.Column("report_deadline", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incidents_agent_id", "incidents", ["agent_id"])

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("email", sa.String(256), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_enabled", sa.Boolean, server_default="false"),
        sa.Column("recovery_key_hash", sa.String(256), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_timeout_hours", sa.Integer, server_default="24"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("priority", sa.String(32), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("created_by", sa.String(256), nullable=True),
        sa.Column("timeout_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("cost_eur", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tasks_agent_id", "tasks", ["agent_id"])

    # --- approvals ---
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(256), nullable=True),
        sa.Column("timeout_minutes", sa.Integer, nullable=False, server_default="60"),
    )
    op.create_index("ix_approvals_agent_id", "approvals", ["agent_id"])

    # --- config_revisions ---
    op.create_table(
        "config_revisions",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("config_json", sa.Text, nullable=False),
        sa.Column("change_description", sa.Text, nullable=False),
        sa.Column("created_by", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agent_id", "version"),
    )
    op.create_index("ix_config_revisions_agent_id", "config_revisions", ["agent_id"])

    # --- agent_memory ---
    op.create_table(
        "agent_memory",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(128)),
        sa.Column("session_id", sa.String(128)),
        sa.Column("role", sa.String(32)),
        sa.Column("content", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_memory_agent_id", "agent_memory", ["agent_id"])
    op.create_index("ix_agent_memory_session_id", "agent_memory", ["session_id"])

    # --- workspace_mounts ---
    op.create_table(
        "workspace_mounts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("collection_name", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workspace_mounts_agent_id", "workspace_mounts", ["agent_id"])
    op.create_index(
        "ix_workspace_agent_collection",
        "workspace_mounts",
        ["agent_id", "collection_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("workspace_mounts")
    op.drop_table("agent_memory")
    op.drop_table("config_revisions")
    op.drop_table("approvals")
    op.drop_table("tasks")
    op.drop_table("users")
    op.drop_table("incidents")
    op.drop_table("audit_log")
    op.drop_table("agents")
