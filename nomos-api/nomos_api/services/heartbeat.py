"""Heartbeat service — tracks agent liveness via DB persistence.

Agents send heartbeats every ~60s. Status classification:
- online:  last heartbeat < 5 minutes ago
- stale:   last heartbeat 5-10 minutes ago
- offline: last heartbeat > 10 minutes ago (or never seen)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent

# Thresholds for status classification
_STALE_THRESHOLD = timedelta(minutes=5)
_OFFLINE_THRESHOLD = timedelta(minutes=10)


async def record_heartbeat(
    db: AsyncSession,
    agent_id: str,
    metrics: dict | None = None,
) -> dict | None:
    """Record a heartbeat for an agent. Returns response dict or None if agent not found."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None

    agent.heartbeat_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(agent)

    return {
        "agent_id": agent.id,
        "status": derive_status(agent.heartbeat_at),
    }


def derive_status(heartbeat_at: datetime | None) -> str:
    """Classify agent liveness from last heartbeat timestamp.

    Returns 'online', 'stale', or 'offline'.
    """
    if heartbeat_at is None:
        return "offline"

    # Ensure timezone-aware comparison (SQLite returns naive datetimes)
    if heartbeat_at.tzinfo is None:
        heartbeat_at = heartbeat_at.replace(tzinfo=timezone.utc)

    elapsed = datetime.now(timezone.utc) - heartbeat_at
    if elapsed > _OFFLINE_THRESHOLD:
        return "offline"
    if elapsed > _STALE_THRESHOLD:
        return "stale"
    return "online"
