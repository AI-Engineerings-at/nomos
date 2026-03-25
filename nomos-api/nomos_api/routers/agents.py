"""Agent endpoints — create, patch (pause/resume/kill), heartbeat, and kill switch."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import AuditLog
from nomos_api.schemas import (
    AgentCreateRequest,
    AgentPatchRequest,
    AgentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from nomos_api.services.agent_service import create_agent
from nomos_api.services.fleet_service import get_agent, update_agent_status
from nomos_api.services.heartbeat import HeartbeatService
from nomos.core.events import EventType
from nomos.core.hash_chain import HashChain

router = APIRouter(prefix="/api", tags=["agents"])

# Singleton heartbeat service for the application lifecycle
_heartbeat_service = HeartbeatService()


def get_heartbeat_service() -> HeartbeatService:
    """Return the shared HeartbeatService instance."""
    return _heartbeat_service


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_new_agent(
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    result = await create_agent(
        db=db,
        name=request.name,
        role=request.role,
        company=request.company,
        email=request.email,
        risk_class=request.risk_class,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return AgentResponse.model_validate(result.agent)


@router.post("/agents/{agent_id}/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat(agent_id: str, request: HeartbeatRequest) -> HeartbeatResponse:
    svc = get_heartbeat_service()
    svc.record(agent_id, request.metrics)
    status = svc.get_status(agent_id)
    return HeartbeatResponse(agent_id=agent_id, status=status)


@router.patch("/agents/{agent_id}", response_model=dict)
async def patch_agent(agent_id: str, request: AgentPatchRequest) -> dict:
    if request.status is None:
        raise HTTPException(status_code=400, detail="No update fields provided")
    return {"agent_id": agent_id, "status": request.status, "updated": True}


@router.post("/agents/{agent_id}/kill", response_model=AgentResponse)
async def kill_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Permanently stop an agent via kill switch.

    Sets agent status to 'killed' and creates an audit trail entry
    for the kill_switch.activated event.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    # Update status to killed
    agent = await update_agent_status(db, agent_id, "killed")

    # Write kill switch event to audit chain on disk
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if agent_dir.is_relative_to(safe_base):
        audit_dir = agent_dir / "audit"
        if audit_dir.exists():
            chain = HashChain(storage_dir=audit_dir)
            entry = chain.append(
                event_type=EventType.KILL_SWITCH_ACTIVATED,
                agent_id=agent_id,
                data={"reason": "kill_switch.activated", "status": "killed"},
            )
            # Persist audit entry to DB
            audit_log = AuditLog(
                agent_id=entry.agent_id,
                sequence=entry.sequence,
                event_type=entry.event_type,
                data=entry.data,
                chain_hash=entry.hash,
                timestamp=entry.timestamp,
            )
            db.add(audit_log)
            await db.commit()

    return AgentResponse.model_validate(agent)
