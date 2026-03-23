"""Agent creation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import AgentCreateRequest, AgentResponse
from nomos_api.services.agent_service import create_agent

router = APIRouter(prefix="/api", tags=["agents"])


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
