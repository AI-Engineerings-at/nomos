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
    importance_score: float = 1.0,
) -> AgentMemory:
    """Persist a single message to the agent_memory table."""
    msg = AgentMemory(
        agent_id=agent_id,
        session_id=session_id,
        role=role,
        content=content,
        importance_score=importance_score,
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


async def prune_messages(
    db: AsyncSession,
    agent_id: str,
    session_id: str,
    keep_recent: int = 50,
) -> int:
    """Delete the oldest non-summary turns for an agent+session pair.

    Retention policy (DSGVO-safe):
    - All ``[SUMMARY]`` rows are ALWAYS retained (they are the durable,
      condensed record of pruned turns — deleting them would lose history).
    - The most recent ``keep_recent`` non-summary turns are retained.
    - Only non-summary turns older than the keep_recent-th newest are deleted.

    Returns the number of rows deleted.
    """
    # Newest-first ids of the non-summary turns for this pair.
    id_stmt = (
        select(AgentMemory.id)
        .where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.session_id == session_id,
            ~AgentMemory.content.startswith("[SUMMARY]"),
        )
        .order_by(AgentMemory.id.desc())
    )
    result = await db.execute(id_stmt)
    ids_newest_first = list(result.scalars().all())

    if len(ids_newest_first) <= keep_recent:
        return 0

    ids_to_delete = ids_newest_first[keep_recent:]

    del_stmt = delete(AgentMemory).where(AgentMemory.id.in_(ids_to_delete))
    del_result = await db.execute(del_stmt)
    await db.commit()
    return del_result.rowcount


async def search_messages(db: AsyncSession, search_term: str) -> list[AgentMemory]:
    """Find all messages containing search_term across all agents (case-insensitive)."""
    stmt = select(AgentMemory).where(func.lower(AgentMemory.content).contains(search_term.lower()))
    result = await db.execute(stmt)
    return list(result.scalars().all())
