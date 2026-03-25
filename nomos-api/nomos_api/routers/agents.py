"""Agent endpoints — create, patch (pause/resume/kill), and heartbeat."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import (
    AgentCreateRequest,
    AgentPatchRequest,
    AgentResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from nomos_api.services.agent_service import create_agent
from nomos_api.services.heartbeat import HeartbeatService

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
