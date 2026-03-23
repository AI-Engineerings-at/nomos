"""SQLAlchemy ORM models for the NomOS fleet registry."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
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
    manifest_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    compliance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    agents_dir: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )


class AuditLog(Base):
    """Indexed audit entries. Source of truth = JSONL chain on disk."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_agent_sequence", "agent_id", "sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
