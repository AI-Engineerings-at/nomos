"""Fleet service — CRUD operations for agent registry."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent


async def list_agents(db: AsyncSession) -> list[Agent]:
    """List all agents in the fleet."""
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


async def get_agent(db: AsyncSession, agent_id: str) -> Agent | None:
    """Get a single agent by ID."""
    return await db.get(Agent, agent_id)


async def update_agent_status(db: AsyncSession, agent_id: str, status: str) -> Agent | None:
    """Update an agent's status."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None
    agent.status = status
    try:
        await db.commit()
        await db.refresh(agent)
    except Exception as exc:
        await db.rollback()
        raise RuntimeError(f"Database error updating agent status: {exc}") from exc
    return agent
