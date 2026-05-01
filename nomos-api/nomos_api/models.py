"""SQLAlchemy ORM models for the NomOS fleet registry."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Float, JSON, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Agent(Base):
    """An AI agent registered in the NomOS fleet."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(256), nullable=False)
    company: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    risk_class: Mapped[str] = mapped_column(String(32), nullable=False, default="limited")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    agents_dir: Mapped[str] = mapped_column(Text, nullable=False)
    budget_used_eur: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    budget_limit_eur: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AuditLog(Base):
    """Indexed audit entries. Source of truth = JSONL chain on disk."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_agent_sequence", "agent_id", "sequence"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)


class IncidentRecord(Base):
    """A detected security or privacy incident (Art. 33/34 DSGVO)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="detected")
    detected_at: Mapped[str] = mapped_column(String(64), nullable=False)
    report_deadline: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base):
    """NomOS user with role-based access, optional 2FA, and recovery key."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")  # admin | user | officer
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)  # None = 2FA not enabled
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_key_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_timeout_hours: Mapped[int] = mapped_column(Integer, default=24)  # 8 for admin, 24 for user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Task(Base):
    """A task assigned to an AI agent."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    cost_eur: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Approval(Base):
    """An approval request for a gated action."""

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)


class ConfigRevision(Base):
    """A versioned snapshot of an agent's configuration."""

    __tablename__ = "config_revisions"
    __table_args__ = (UniqueConstraint("agent_id", "version"),)

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_description: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentMemory(Base):
    """Persistent memory store for agent conversations — replaces fake HonchoClient."""

    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    importance_score: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkspaceMount(Base):
    """A mounted collection in an agent's workspace."""

    __tablename__ = "workspace_mounts"
    __table_args__ = (Index("ix_workspace_agent_collection", "agent_id", "collection_name", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    collection_name: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AlertRule(Base):
    """Configuration for alert thresholds and notifications."""

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    threshold_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'above', 'below', 'change'
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    comparison_window: Mapped[str | None] = mapped_column(String(50))  # e.g., '5m', '1h'
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'critical', 'warning', 'info'
    notification_channels: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"email": [...], "webhook": [...]}
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Alert(Base):
    """Record of triggered alerts and their resolution status."""

    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_status", "status"), Index("ix_alerts_severity", "severity"))

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # 'pending', 'sent', 'failed'
    notification_channels: Mapped[dict] = mapped_column(JSON, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="triggered"
    )  # 'triggered', 'acknowledged', 'resolved'


class Metric(Base):
    """Time-series metrics for monitoring system performance."""

    __tablename__ = "metrics"
    __table_args__ = (
        Index("ix_metrics_timestamp", "timestamp"),
        Index("ix_metrics_name", "metric_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dimensions: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"endpoint": "/api/agents", "method": "GET"}
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))  # 'api', 'agent', 'system'
