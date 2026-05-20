"""Cost endpoints — budget overview per agent and across fleet, DB-backed."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import require_admin, require_agent_actor
from nomos_api.database import get_db
from nomos_api.models import Agent, User
from nomos_api.schemas import CostOverviewResponse, CostResponse
from nomos_api.services.budget import get_all_costs

router = APIRouter(prefix="/api", tags=["costs"])


@router.get("/costs", response_model=CostOverviewResponse)
async def get_costs(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> CostOverviewResponse:
    """Return budget status for all agents. Admin-only — cross-tenant
    spend disclosure (L035 audit A-C7)."""
    costs = await get_all_costs(db)
    return CostOverviewResponse(
        costs=[CostResponse(**c) for c in costs],
        total=len(costs),
    )


@router.get("/costs/{agent_id}", response_model=CostResponse)
async def get_agent_cost(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _actor: Agent = Depends(require_agent_actor),
) -> CostResponse:
    """Return budget status for a single agent. Caller must own the agent
    or be admin (L035 audit A-C7)."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    current = agent.budget_used_eur
    limit = agent.budget_limit_eur
    percent_used = (current / limit * 100) if limit > 0 else 0.0

    if current >= limit:
        status = "exceeded"
    elif percent_used >= 80.0:
        status = "warning"
    else:
        status = "normal"

    return CostResponse(
        agent_id=agent_id,
        total_cost_eur=current,
        budget_limit_eur=limit,
        budget_status=status,
        percent_used=round(percent_used, 2),
    )
