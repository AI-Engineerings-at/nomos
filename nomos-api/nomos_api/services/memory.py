"""Agent memory service — DB-backed, replaces fake HonchoClient."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import AgentMemory


async def store_message(
    db: AsyncSession,
    agent_id: str,
    session_id: str,
    role: str,
    content: str,
) -> AgentMemory:
    """Persist a single message to the agent_memory table."""
    msg = AgentMemory(
        agent_id=agent_id,
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_messages(
    db: AsyncSession,
    agent_id: str,
    session_id: str,
) -> list[AgentMemory]:
    """Return all messages for an agent+session pair, ordered by insertion."""
    stmt = (
        select(AgentMemory)
        .where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.session_id == session_id,
        )
        .order_by(AgentMemory.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_by_agent(db: AsyncSession, agent_id: str) -> int:
    """Delete all memory entries for a given agent. Returns deleted count."""
    stmt = delete(AgentMemory).where(AgentMemory.agent_id == agent_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def delete_by_content(db: AsyncSession, search_term: str) -> int:
    """Delete messages containing search_term (DSGVO Art. 17). Returns deleted count."""
    stmt = delete(AgentMemory).where(func.lower(AgentMemory.content).contains(search_term.lower()))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def search_messages(db: AsyncSession, search_term: str) -> list[AgentMemory]:
    """Find all messages containing search_term across all agents (case-insensitive)."""
    stmt = select(AgentMemory).where(func.lower(AgentMemory.content).contains(search_term.lower()))
    result = await db.execute(stmt)
    return list(result.scalars().all())
