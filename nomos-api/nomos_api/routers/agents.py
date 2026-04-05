"""Agent endpoints — create, patch, heartbeat, pause, resume, kill, retire."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import check_agent_access
from nomos_api.database import get_db
from nomos_api.models import Agent, User
from nomos_api.routers.auth import get_current_user
from nomos_api.schemas import (
    AgentCreateRequest,
    AgentPatchRequest,
    AgentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from nomos_api.services.agent_service import create_agent, check_fcl_limit_with_message
from nomos_api.services.audit import write_audit_event as _write_audit_event
from nomos_api.services.fleet_service import get_agent, update_agent_status
from nomos_api.services.heartbeat import record_heartbeat as _record_heartbeat
from nomos.core.events import EventType

router = APIRouter(prefix="/api", tags=["agents"])


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
async def record_heartbeat(
    agent_id: str,
    request: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
) -> HeartbeatResponse:
    result = await _record_heartbeat(db, agent_id, request.metrics)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return HeartbeatResponse(agent_id=result["agent_id"], status=result["status"])


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def patch_agent(
    agent_id: str,
    request: AgentPatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    if request.status is None:
        raise HTTPException(status_code=400, detail="No update fields provided")
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    check_agent_access(user, agent, "patch")
    agent = await update_agent_status(db, agent_id, request.status)
    return AgentResponse.model_validate(agent, from_attributes=True)


@router.post("/agents/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Pause an agent. Any authenticated user can pause their own agents.

    Sets agent status to 'paused' and creates an audit trail entry
    for the kill_switch.user_pause event (Art. 14 EU AI Act).
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    check_agent_access(user, agent, "pause")
    if agent.status in ("paused", "killed", "retired"):
        raise HTTPException(status_code=409, detail=f"Agent is already {agent.status}")

    agent = await update_agent_status(db, agent_id, "paused")

    await _write_audit_event(
        db,
        agent,
        agent_id,
        EventType.KILL_SWITCH_USER_PAUSE,
        {"reason": "kill_switch.user_pause", "status": "paused"},
    )

    if user.role == "admin" and agent.email != user.email:
        await _write_audit_event(
            db,
            agent,
            agent_id,
            EventType.ADMIN_ACTION,
            {"action": "pause", "admin_email": user.email, "agent_owner": agent.email},
        )

    return AgentResponse.model_validate(agent)


@router.post("/agents/{agent_id}/resume", response_model=AgentResponse)
async def resume_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Resume a paused agent. Only allowed when agent is currently paused.

    Sets agent status to 'running' and creates an audit trail entry.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    check_agent_access(user, agent, "resume")

    if agent.status != "paused":
        raise HTTPException(
            status_code=409,
            detail=f"Agent {agent_id!r} is not paused (current status: {agent.status!r})",
        )

    agent = await update_agent_status(db, agent_id, "running")

    await _write_audit_event(
        db,
        agent,
        agent_id,
        EventType.AGENT_DEPLOYED,
        {"reason": "agent.resumed", "status": "running", "previous_status": "paused"},
    )

    if user.role == "admin" and agent.email != user.email:
        await _write_audit_event(
            db,
            agent,
            agent_id,
            EventType.ADMIN_ACTION,
            {"action": "resume", "admin_email": user.email, "agent_owner": agent.email},
        )

    return AgentResponse.model_validate(agent)


@router.post("/agents/{agent_id}/kill", response_model=AgentResponse)
async def kill_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Permanently stop an agent via kill switch.

    Sets agent status to 'killed' and creates an audit trail entry
    for the kill_switch.activated event.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    check_agent_access(user, agent, "kill")

    agent = await update_agent_status(db, agent_id, "killed")

    await _write_audit_event(
        db,
        agent,
        agent_id,
        EventType.KILL_SWITCH_ACTIVATED,
        {"reason": "kill_switch.activated", "status": "killed"},
    )

    if user.role == "admin" and agent.email != user.email:
        await _write_audit_event(
            db,
            agent,
            agent_id,
            EventType.ADMIN_ACTION,
            {"action": "kill", "admin_email": user.email, "agent_owner": agent.email},
        )

    return AgentResponse.model_validate(agent)


@router.post("/agents/{agent_id}/retire", response_model=AgentResponse)
async def retire_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Gracefully retire an agent — revoke access, unmount collections, archive.

    Sets agent status to 'retired' and creates an audit trail entry
    for the agent.retired event.
    """
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    check_agent_access(user, agent, "retire")

    agent = await update_agent_status(db, agent_id, "retired")

    await _write_audit_event(
        db,
        agent,
        agent_id,
        EventType.AGENT_RETIRED,
        {"reason": "agent.retired", "status": "retired"},
    )

    if user.role == "admin" and agent.email != user.email:
        await _write_audit_event(
            db,
            agent,
            agent_id,
            EventType.ADMIN_ACTION,
            {"action": "retire", "admin_email": user.email, "agent_owner": agent.email},
        )

    return AgentResponse.model_validate(agent)
