"""Workspace service — DB-backed agent workspace isolation.

Each agent implicitly has a workspace (identified by agent_id).
Collections can be mounted/unmounted per agent workspace.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent, WorkspaceMount


async def agent_exists(db: AsyncSession, agent_id: str) -> bool:
    """Check whether an agent exists in the database."""
    stmt = select(Agent.id).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_mounted_collections(db: AsyncSession, agent_id: str) -> list[str]:
    """Return list of mounted collection names for an agent."""
    stmt = select(WorkspaceMount.collection_name).where(WorkspaceMount.agent_id == agent_id).order_by(WorkspaceMount.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mount_collection(db: AsyncSession, agent_id: str, collection_name: str) -> bool:
    """Mount a collection into an agent's workspace. Idempotent.

    Returns True if the mount exists after the call.
    """
    # Check if already mounted
    stmt = select(WorkspaceMount.id).where(
        WorkspaceMount.agent_id == agent_id,
        WorkspaceMount.collection_name == collection_name,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        return True

    mount = WorkspaceMount(agent_id=agent_id, collection_name=collection_name)
    db.add(mount)
    await db.commit()
    return True


async def unmount_collection(db: AsyncSession, agent_id: str, collection_name: str) -> bool:
    """Unmount a collection from an agent's workspace.

    Returns True if the collection was found and removed, False otherwise.
    """
    stmt = delete(WorkspaceMount).where(
        WorkspaceMount.agent_id == agent_id,
        WorkspaceMount.collection_name == collection_name,
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
