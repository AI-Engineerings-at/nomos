"""Budget service — DB-backed per-agent cost tracking and enforcement.

Reads budget_used_eur and budget_limit_eur from the Agent model.
No in-memory state. All data persisted via SQLAlchemy async sessions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent


async def check_budget(
    db: AsyncSession,
    agent_id: str,
    estimated_cost: float,
    warn_at: float = 80.0,
) -> dict | None:
    """Check if an agent has budget for the estimated cost.

    Returns None if agent not found (caller should raise 404).
    Returns dict with: allowed, status, remaining, percent_used, current, limit, agent_id.
    """
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None

    current = agent.budget_used_eur
    limit = agent.budget_limit_eur
    projected = current + estimated_cost
    percent_used = (projected / limit * 100) if limit > 0 else 0.0

    if projected >= limit:
        status = "exceeded"
        allowed = False
    elif percent_used >= warn_at:
        status = "warning"
        allowed = True
    else:
        status = "normal"
        allowed = True

    return {
        "allowed": allowed,
        "status": status,
        "remaining": max(0.0, limit - projected),
        "percent_used": round(percent_used, 2),
        "current": current,
        "limit": limit,
        "agent_id": agent_id,
    }


async def track_cost(
    db: AsyncSession,
    agent_id: str,
    cost: float,
) -> dict | None:
    """Add cost to an agent's budget_used_eur. Returns None if agent not found."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None

    agent.budget_used_eur += cost
    await db.commit()
    await db.refresh(agent)

    return {
        "agent_id": agent_id,
        "budget_used_eur": agent.budget_used_eur,
        "budget_limit_eur": agent.budget_limit_eur,
    }


async def get_all_costs(db: AsyncSession) -> list[dict]:
    """Return budget status for all agents."""
    result = await db.execute(select(Agent))
    agents = result.scalars().all()

    costs: list[dict] = []
    for agent in agents:
        current = agent.budget_used_eur
        limit = agent.budget_limit_eur
        percent_used = (current / limit * 100) if limit > 0 else 0.0

        if current >= limit:
            status = "exceeded"
        elif percent_used >= 80.0:
            status = "warning"
        else:
            status = "normal"

        costs.append(
            {
                "agent_id": agent.id,
                "total_cost_eur": current,
                "budget_limit_eur": limit,
                "budget_status": status,
                "percent_used": round(percent_used, 2),
            }
        )

    return costs
