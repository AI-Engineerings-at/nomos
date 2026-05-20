"""Budget endpoints — check and track per-agent costs via DB."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import authorize_agent_action
from nomos_api.database import get_db
from nomos_api.schemas import BudgetCheckRequest, BudgetTrackRequest, BudgetTrackResponse
from nomos_api.services.budget import check_budget, track_cost

router = APIRouter(prefix="/api", tags=["budget"])


@router.post("/budget/check")
async def budget_check(
    request: BudgetCheckRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if agent has budget. Caller must own the agent or be admin /
    service principal (L035 audit A-C7 — was unguarded). Unknown agents
    get restrictive default (fail-closed)."""
    await authorize_agent_action(
        db=db, request=http_request, agent_id=request.agent_id, action="budget_check", allow_missing=True
    )
    result = await check_budget(db, request.agent_id, request.estimated_cost)
    if result is None:
        return {
            "allowed": False,
            "remaining": 0,
            "status": "unknown_agent",
            "reason": f"Agent {request.agent_id!r} not registered. Register the agent first.",
            "agent_id": request.agent_id,
        }
    return result


@router.post("/budget/track", response_model=BudgetTrackResponse)
async def budget_track(
    request: BudgetTrackRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> BudgetTrackResponse:
    """Track a cost against an agent's budget. Caller must own the agent
    or be admin / service principal (L035 audit A-C7)."""
    await authorize_agent_action(
        db=db, request=http_request, agent_id=request.agent_id, action="budget_track", allow_missing=True
    )
    result = await track_cost(db, request.agent_id, request.cost)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id!r} not found")
    return BudgetTrackResponse(**result)
