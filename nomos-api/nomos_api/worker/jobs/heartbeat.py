"""Stale Agent Detection — mark agents without recent heartbeat as stale.

Runs every 5 minutes. Agents with status='running' and no heartbeat within
the threshold are marked 'stale'.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos_api.models import Agent

logger = logging.getLogger("nomos.worker.heartbeat")

_DEFAULT_STALE_THRESHOLD_MINUTES = 10


async def detect_stale_agents(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
    stale_threshold_minutes: int = _DEFAULT_STALE_THRESHOLD_MINUTES,
) -> int:
    """Detect and mark stale agents.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        session_factory: Override for testing. Production uses module-level factory.
        stale_threshold_minutes: Minutes without heartbeat before marking stale.

    Returns:
        Number of agents marked stale.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_threshold_minutes)

    # v0.4.0 (Q / audit D-#16): wrap the SQL block so a transient DB
    # failure here logs once and re-raises — ARQ then handles retry vs
    # final-fail per its own policy. Previously this job had NO
    # try/catch, so a single DB outage spammed the ARQ retry queue
    # without any context in logs.
    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Agent.id).where(
                    Agent.status == "running",
                    Agent.heartbeat_at < cutoff,
                )
            )
            stale_ids: list[str] = list(result.scalars().all())

            if not stale_ids:
                return 0

            await session.execute(update(Agent).where(Agent.id.in_(stale_ids)).values(status="stale"))
            await session.commit()
    except Exception:
        logger.exception("detect_stale_agents failed cutoff=%s", cutoff.isoformat())
        raise

    logger.warning("Stale agents detected: %s", stale_ids)
    return len(stale_ids)
