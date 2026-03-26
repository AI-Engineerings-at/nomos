"""Config revision service — DB-backed versioned snapshots of agent configurations.

Supports saving new revisions, listing history, retrieving the latest,
and rolling back to a specific version.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import ConfigRevision


async def save_revision(
    db: AsyncSession,
    agent_id: str,
    config_json: dict,
    change_description: str,
    created_by: str | None = None,
) -> ConfigRevision:
    """Save a new config revision. Auto-increments version number."""
    # Get the current max version for this agent
    result = await db.execute(select(func.max(ConfigRevision.version)).where(ConfigRevision.agent_id == agent_id))
    max_version = result.scalar_one_or_none()
    version = (max_version or 0) + 1

    revision = ConfigRevision(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        version=version,
        config_json=json.dumps(config_json),
        change_description=change_description,
        created_by=created_by,
    )
    db.add(revision)
    await db.commit()
    await db.refresh(revision)
    return revision


async def get_latest(
    db: AsyncSession,
    agent_id: str,
) -> ConfigRevision | None:
    """Get the latest revision for an agent, or None if no revisions exist."""
    result = await db.execute(
        select(ConfigRevision)
        .where(ConfigRevision.agent_id == agent_id)
        .order_by(ConfigRevision.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_revisions(
    db: AsyncSession,
    agent_id: str,
) -> list[ConfigRevision]:
    """List all revisions for an agent, ordered by version ascending."""
    result = await db.execute(
        select(ConfigRevision).where(ConfigRevision.agent_id == agent_id).order_by(ConfigRevision.version.asc())
    )
    return list(result.scalars().all())


async def rollback(
    db: AsyncSession,
    agent_id: str,
    version: int,
) -> ConfigRevision | None:
    """Retrieve the revision for a specific version.

    Returns None if agent_id/version combination not found.
    """
    result = await db.execute(
        select(ConfigRevision).where(
            ConfigRevision.agent_id == agent_id,
            ConfigRevision.version == version,
        )
    )
    return result.scalar_one_or_none()
