"""Incident management endpoints — Art. 33/34 DSGVO compliance."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import (
    IncidentCreateRequest,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdateRequest,
)
from nomos_api.services.incident import create_incident, list_incidents, update_incident_status

router = APIRouter(prefix="/api", tags=["incidents"])


@router.post("/incidents", response_model=IncidentResponse | None, status_code=201)
async def create_new_incident(
    request: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse | None:
    """Analyze a log entry and create an incident if detected."""
    record = await create_incident(
        db=db,
        agent_id=request.agent_id,
        log_entry=request.log_entry,
        context=request.context,
    )
    if record is None:
        raise HTTPException(
            status_code=204,
            detail="No incident detected in log entry",
        )
    return IncidentResponse(
        id=record.id,
        agent_id=record.agent_id,
        incident_type=record.incident_type,
        description=record.description,
        severity=record.severity,
        status=record.status,
        detected_at=record.detected_at,
        report_deadline=record.report_deadline,
    )


@router.get("/incidents", response_model=IncidentListResponse)
async def get_incidents(
    db: AsyncSession = Depends(get_db),
) -> IncidentListResponse:
    """List all incidents."""
    records = await list_incidents(db)
    return IncidentListResponse(
        incidents=[
            IncidentResponse(
                id=r.id,
                agent_id=r.agent_id,
                incident_type=r.incident_type,
                description=r.description,
                severity=r.severity,
                status=r.status,
                detected_at=r.detected_at,
                report_deadline=r.report_deadline,
            )
            for r in records
        ],
        total=len(records),
    )


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    request: IncidentUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Update incident status (detected -> reported -> resolved)."""
    record = await update_incident_status(db, incident_id, request.status)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return IncidentResponse(
        id=record.id,
        agent_id=record.agent_id,
        incident_type=record.incident_type,
        description=record.description,
        severity=record.severity,
        status=record.status,
        detected_at=record.detected_at,
        report_deadline=record.report_deadline,
    )
