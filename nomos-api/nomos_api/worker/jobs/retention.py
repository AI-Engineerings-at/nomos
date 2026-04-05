"""DSGVO Retention Cleanup — delete agent memory older than retention_days.

Runs daily at 03:00. Complies with Art. 5(1)(e) GDPR (storage limitation).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos_api.models import AgentMemory

logger = logging.getLogger("nomos.worker.retention")


async def retention_cleanup(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
    retention_days: int | None = None,
) -> int:
    """Delete agent memory messages older than retention_days.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        session_factory: Override for testing. Production uses module-level factory.
        retention_days: Override for testing. Production uses settings.

    Returns:
        Number of deleted rows.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    if retention_days is None:
        from nomos_api.config import settings

        retention_days = settings.retention_days

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    async with session_factory() as session:
        result = await session.execute(delete(AgentMemory).where(AgentMemory.created_at < cutoff))
        deleted_count: int = result.rowcount  # type: ignore[assignment]
        await session.commit()

    if deleted_count > 0:
        logger.info("DSGVO retention: deleted %d messages older than %d days", deleted_count, retention_days)

    return deleted_count
