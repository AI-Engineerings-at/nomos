"""Fleet endpoints — list and get agents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import AgentResponse, FleetResponse
from nomos_api.services.fleet_service import get_agent, list_agents

router = APIRouter(prefix="/api", tags=["fleet"])


@router.get("/fleet", response_model=FleetResponse)
async def get_fleet(db: AsyncSession = Depends(get_db)) -> FleetResponse:
    agents = await list_agents(db)
    return FleetResponse(agents=[AgentResponse.model_validate(a) for a in agents], total=len(agents))


@router.get("/fleet/{agent_id}", response_model=AgentResponse)
async def get_fleet_agent(agent_id: str, db: AsyncSession = Depends(get_db)) -> AgentResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return AgentResponse.model_validate(agent)
