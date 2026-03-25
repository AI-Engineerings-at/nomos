"""Cost endpoints — budget overview per agent and across fleet."""

from __future__ import annotations

from fastapi import APIRouter

from nomos_api.schemas import CostOverviewResponse, CostResponse
from nomos_api.services.budget import BudgetService

router = APIRouter(prefix="/api", tags=["costs"])

# Singleton service instance for the application lifecycle
_budget_service = BudgetService()


def get_budget_service() -> BudgetService:
    """Return the shared BudgetService instance."""
    return _budget_service


@router.get("/costs", response_model=CostOverviewResponse)
async def get_costs() -> CostOverviewResponse:
    svc = get_budget_service()
    costs = []
    for agent_id, total in svc._costs.items():
        limit = 50.0  # default from BudgetConfig
        result = svc.check(agent_id, current=total, limit=limit, warn_at=80)
        costs.append(CostResponse(
            agent_id=agent_id,
            total_cost_eur=total,
            budget_limit_eur=limit,
            budget_status=result["status"],
            percent_used=result["percent_used"],
        ))
    return CostOverviewResponse(costs=costs, total=len(costs))


@router.get("/costs/{agent_id}", response_model=CostResponse)
async def get_agent_cost(agent_id: str) -> CostResponse:
    svc = get_budget_service()
    total = svc.get_total(agent_id)
    limit = 50.0  # default from BudgetConfig
    result = svc.check(agent_id, current=total, limit=limit, warn_at=80)
    return CostResponse(
        agent_id=agent_id,
        total_cost_eur=total,
        budget_limit_eur=limit,
        budget_status=result["status"],
        percent_used=result["percent_used"],
    )
