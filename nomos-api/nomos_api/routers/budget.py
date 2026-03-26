"""Budget check endpoint — called by NomOS Plugin before_tool_call hook."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from nomos_api.services.budget import BudgetService

router = APIRouter(prefix="/api", tags=["budget"])

_budget_service = BudgetService()


class BudgetCheckRequest(BaseModel):
    agent_id: str
    estimated_cost: float = 0.0


@router.post("/budget/check")
async def check_budget(request: BudgetCheckRequest) -> dict:
    """Check if agent has budget for estimated cost.

    NOTE: BudgetService uses in-memory tracking (known limitation).
    Default limit 100 EUR, warn_at 80%. To be replaced with DB-backed service.
    """
    current = _budget_service._costs.get(request.agent_id, 0.0)
    projected = current + request.estimated_cost
    limit = 100.0
    warn_at = 80
    result = _budget_service.check(request.agent_id, projected, limit, warn_at)
    return {
        "allowed": result.get("allowed", True),
        "remaining": max(0, limit - projected),
        "status": result.get("status", "normal"),
        "error": None if result.get("allowed") else "Budget exceeded",
    }
