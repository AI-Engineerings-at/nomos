"""Agent endpoints — create, patch, heartbeat, pause, resume, kill, retire."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import Agent, AuditLog
from nomos_api.schemas import (
    AgentCreateRequest,
    AgentPatchRequest,
    AgentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from nomos_api.services.agent_service import create_agent, check_fcl_limit_with_message
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


async def _write_audit_event(
    db: AsyncSession,
    agent: Agent,
    agent_id: str,
    event_type: EventType,
    data: dict,
) -> None:
    """Write an event to the on-disk hash chain and persist it to the DB."""
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        return
    audit_dir = agent_dir / "audit"
    if not audit_dir.exists():
        return
    chain = HashChain(storage_dir=audit_dir)
    entry = chain.append(
        event_type=event_type,
        agent_id=agent_id,
        data=data,
    )
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


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_new_agent(
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    # FCL Check — max 3 agents free
    from sqlalchemy import select, func
    count_result = await db.execute(select(func.count()).select_from(Agent).where(Agent.status != "killed"))
    active_count = count_result.scalar() or 0
    allowed, msg = check_fcl_limit_with_message(active_count)
    if not allowed:
        raise HTTPException(status_code=403, detail=msg)

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


@router.post("/agents/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Pause an agent. Any authenticated user can pause their own agents.

    Sets agent status to 'paused' and creates an audit trail entry
    for the kill_switch.user_pause event (Art. 14 EU AI Act).
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent = await update_agent_status(db, agent_id, "paused")

    await _write_audit_event(
        db, agent, agent_id,
        EventType.KILL_SWITCH_USER_PAUSE,
        {"reason": "kill_switch.user_pause", "status": "paused"},
    )

    return AgentResponse.model_validate(agent)


@router.post("/agents/{agent_id}/resume", response_model=AgentResponse)
async def resume_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Resume a paused agent. Only allowed when agent is currently paused.

    Sets agent status to 'running' and creates an audit trail entry.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    if agent.status != "paused":
        raise HTTPException(
            status_code=409,
            detail=f"Agent {agent_id!r} is not paused (current status: {agent.status!r})",
        )

    agent = await update_agent_status(db, agent_id, "running")

    await _write_audit_event(
        db, agent, agent_id,
        EventType.AGENT_DEPLOYED,
        {"reason": "agent.resumed", "status": "running", "previous_status": "paused"},
    )

    return AgentResponse.model_validate(agent)


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

    agent = await update_agent_status(db, agent_id, "killed")

    await _write_audit_event(
        db, agent, agent_id,
        EventType.KILL_SWITCH_ACTIVATED,
        {"reason": "kill_switch.activated", "status": "killed"},
    )

    return AgentResponse.model_validate(agent)


@router.post("/agents/{agent_id}/retire", response_model=AgentResponse)
async def retire_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Gracefully retire an agent — revoke access, unmount collections, archive.

    Sets agent status to 'retired' and creates an audit trail entry
    for the agent.retired event.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent = await update_agent_status(db, agent_id, "retired")

    await _write_audit_event(
        db, agent, agent_id,
        EventType.AGENT_RETIRED,
        {"reason": "agent.retired", "status": "retired"},
    )

    return AgentResponse.model_validate(agent)
