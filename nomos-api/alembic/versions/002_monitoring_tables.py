"""Add monitoring tables: alert_rules, alerts, metrics.

Revision ID: monitoring_tables
Revises: 001_initial_schema
Create Date: 2026-04-13 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "monitoring_tables"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create alert_rules table
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("threshold_type", sa.String(length=50), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("comparison_window", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("notification_channels", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_rules_metric_name"), "alert_rules", ["metric_name"], unique=False)

    # Create alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("notification_channels", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'triggered'")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_alerts_metric_name"), "alerts", ["metric_name"], unique=False)

    # Create metrics table
    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_metrics_timestamp"), "metrics", ["timestamp"], unique=False)
    op.create_index(op.f("ix_metrics_name"), "metrics", ["metric_name"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f("ix_metrics_name"), table_name="metrics")
    op.drop_index(op.f("ix_metrics_timestamp"), table_name="metrics")
    op.drop_table("metrics")

    op.drop_index(op.f("ix_alerts_metric_name"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_severity"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_status"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_alert_rules_metric_name"), table_name="alert_rules")
    op.drop_table("alert_rules")
