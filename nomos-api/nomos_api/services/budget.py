"""Budget service — tracks and enforces per-agent cost limits.

Provides budget checking (normal/warning/exceeded) and cumulative cost tracking.
The check() method evaluates current spending against the configured limit
and warning threshold percentage.
"""

from __future__ import annotations


class BudgetService:
    """In-memory budget tracker for agent cost enforcement."""

    def __init__(self) -> None:
        self._costs: dict[str, float] = {}

    def check(self, agent_id: str, current: float, limit: float, warn_at: int) -> dict:
        """Check budget status for an agent.

        Args:
            agent_id: The agent identifier.
            current: Current total spend in EUR.
            limit: Monthly budget cap in EUR.
            warn_at: Warning threshold as percentage (e.g. 80 means 80%).

        Returns:
            Dict with keys: allowed, status, percent_used, current, limit.
        """
        percent_used = (current / limit * 100) if limit > 0 else 0.0

        if current >= limit:
            status = "exceeded"
            allowed = False
        elif percent_used >= warn_at:
            status = "warning"
            allowed = True
        else:
            status = "normal"
            allowed = True

        return {
            "allowed": allowed,
            "status": status,
            "percent_used": percent_used,
            "current": current,
            "limit": limit,
            "agent_id": agent_id,
        }

    def track(self, agent_id: str, cost: float) -> None:
        """Add a cost entry for an agent."""
        self._costs[agent_id] = self._costs.get(agent_id, 0.0) + cost

    def get_total(self, agent_id: str) -> float:
        """Get the total accumulated cost for an agent."""
        return self._costs.get(agent_id, 0.0)
