"""Heartbeat service — tracks agent liveness via periodic pings.

Agents send heartbeats every ~60s. The service classifies agents as:
- online: last heartbeat < 5 minutes ago
- stale:  last heartbeat 5-10 minutes ago
- offline: last heartbeat > 10 minutes ago (or never seen)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta


# Thresholds for status classification
_STALE_THRESHOLD = timedelta(minutes=5)
_OFFLINE_THRESHOLD = timedelta(minutes=10)


class HeartbeatService:
    """In-memory heartbeat tracker for agent liveness monitoring."""

    def __init__(self) -> None:
        self._last_seen: dict[str, datetime] = {}
        self._metrics: dict[str, dict] = {}

    def record(self, agent_id: str, metrics: dict) -> None:
        """Record a heartbeat from an agent with optional metrics."""
        self._last_seen[agent_id] = datetime.now(timezone.utc)
        self._metrics[agent_id] = metrics

    def get_status(self, agent_id: str) -> str:
        """Return the liveness status of an agent: online, stale, or offline."""
        last = self._last_seen.get(agent_id)
        if last is None:
            return "offline"

        elapsed = datetime.now(timezone.utc) - last
        if elapsed > _OFFLINE_THRESHOLD:
            return "offline"
        if elapsed > _STALE_THRESHOLD:
            return "stale"
        return "online"

    def get_metrics(self, agent_id: str) -> dict | None:
        """Return the latest metrics for an agent, or None if unknown."""
        return self._metrics.get(agent_id)

    def get_all_statuses(self) -> dict[str, str]:
        """Return status for all known agents."""
        return {agent_id: self.get_status(agent_id) for agent_id in self._last_seen}
