"""Incident 72h Notification — escalate incidents approaching DSGVO deadline.

Runs hourly. Art. 33 DSGVO requires incident notification within 72 hours.
Incidents within 4 hours of deadline are escalated; past deadline are overdue.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos_api.models import IncidentRecord

logger = logging.getLogger("nomos.worker.incidents")

_ESCALATION_THRESHOLD_HOURS = 4


async def check_incident_deadlines(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
) -> dict[str, int]:
    """Check incident deadlines and escalate or mark overdue.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        session_factory: Override for testing. Production uses module-level factory.

    Returns:
        Dict with counts: {"escalated": N, "overdue": M}.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    now = datetime.now(timezone.utc)
    escalation_window = now + timedelta(hours=_ESCALATION_THRESHOLD_HOURS)

    counts: dict[str, int] = {"escalated": 0, "overdue": 0}

    async with session_factory() as session:
        # Only process detected incidents (not already escalated/overdue/resolved)
        result = await session.execute(
            select(IncidentRecord).where(IncidentRecord.status.in_(["detected", "escalated"]))
        )
        incidents = result.scalars().all()

        for incident in incidents:
            deadline = datetime.fromisoformat(incident.report_deadline)
            # Ensure timezone-aware comparison
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            if deadline <= now:
                # Past deadline
                incident.status = "overdue"
                counts["overdue"] += 1
                logger.error(
                    "Incident %d OVERDUE — deadline was %s",
                    incident.id,
                    incident.report_deadline,
                )
            elif deadline <= escalation_window and incident.status == "detected":
                # Within escalation window
                incident.status = "escalated"
                counts["escalated"] += 1
                logger.warning(
                    "Incident %d ESCALATED — deadline in < %dh: %s",
                    incident.id,
                    _ESCALATION_THRESHOLD_HOURS,
                    incident.report_deadline,
                )

        await session.commit()

    return counts
