"""Retention Engine — enforces data retention policies by session age.

Works with timestamps to determine which sessions have exceeded their
retention period and should be deleted. Produces audit events for
compliance tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class RetentionResult:
    """Result of a retention enforcement run."""

    deleted_count: int
    deleted_ids: list[str]
    audit_event: str


@dataclass
class RetentionEngine:
    """Enforces session retention by deleting sessions older than retention_days."""

    retention_days: int
    _sessions: dict[str, datetime] = field(default_factory=dict)

    def add_session(self, session_id: str, created_at: datetime) -> None:
        """Register a session with its creation timestamp."""
        self._sessions[session_id] = created_at

    def enforce(self) -> RetentionResult:
        """Delete all sessions older than retention_days and return the result.

        Sessions exactly at the boundary (age == retention_days) are kept.
        Only sessions strictly older than retention_days are deleted.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        expired = [
            sid
            for sid, created in self._sessions.items()
            if created < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]

        return RetentionResult(
            deleted_count=len(expired),
            deleted_ids=expired,
            audit_event="data.retention_enforced" if expired else "",
        )
