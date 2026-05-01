"""Alert Processing Job — check alert rules and trigger notifications.

Runs every minute to evaluate current metrics against configured thresholds
and create alerts when thresholds are breached.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos_api.services.metrics import AlertService

logger = logging.getLogger("nomos.worker.alerts")


async def process_alerts(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
) -> int:
    """Check all alert rules and trigger notifications.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        session_factory: Override for testing. Production uses module-level factory.

    Returns:
        Number of new alerts triggered.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    async with session_factory() as session:
        alert_service = AlertService(session)
        triggered_count = await alert_service.check_alerts()

        logger.info("Alert processing completed — %d new alerts triggered", triggered_count)
        return triggered_count
