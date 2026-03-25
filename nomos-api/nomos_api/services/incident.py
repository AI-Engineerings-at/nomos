"""Incident service — detect, create, and manage incidents."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import IncidentRecord
from nomos.core.incident import detect_incident


async def create_incident(
    db: AsyncSession,
    agent_id: str,
    log_entry: str,
    context: dict | None = None,
) -> IncidentRecord | None:
    """Detect an incident from a log entry and persist it.

    Returns the created IncidentRecord if an incident was detected, None otherwise.
    """
    incident = detect_incident(log_entry, context)
    if incident is None:
        return None

    record = IncidentRecord(
        agent_id=agent_id,
        incident_type=incident.incident_type.value,
        description=incident.description,
        severity=incident.severity,
        status="detected",
        detected_at=incident.detected_at.isoformat(),
        report_deadline=incident.report_deadline.isoformat(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_incidents(db: AsyncSession) -> list[IncidentRecord]:
    """List all incidents, newest first."""
    result = await db.execute(
        select(IncidentRecord).order_by(IncidentRecord.id.desc())
    )
    return list(result.scalars().all())


async def update_incident_status(
    db: AsyncSession,
    incident_id: int,
    status: str,
) -> IncidentRecord | None:
    """Update incident status (detected -> reported -> resolved)."""
    result = await db.execute(
        select(IncidentRecord).where(IncidentRecord.id == incident_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None

    record.status = status
    await db.commit()
    await db.refresh(record)
    return record
