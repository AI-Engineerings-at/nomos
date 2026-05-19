"""Approval service — DB-backed approval queue for gated agent actions.

Actions that require human sign-off (e.g. external API calls, file deletion,
data export) are submitted as approval requests and must be explicitly
approved or denied before the agent can proceed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Approval

_VALID_RESOLUTIONS = {"approved", "denied"}


async def create_approval(
    db: AsyncSession,
    agent_id: str,
    action: str,
    description: str,
    timeout_minutes: int = 60,
) -> Approval:
    """Create a new approval request in 'pending' status."""
    approval = Approval(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        action=action,
        description=description,
        status="pending",
        timeout_minutes=timeout_minutes,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


async def resolve_approval(
    db: AsyncSession,
    approval_id: str,
    resolution: str,
    resolved_by: str,
) -> Approval | None:
    """Approve or deny a pending request. Returns None if not found.

    Raises ValueError if resolution is not 'approved' or 'denied'.
    """
    if resolution not in _VALID_RESOLUTIONS:
        raise ValueError(f"Invalid resolution: {resolution!r}. Must be one of {sorted(_VALID_RESOLUTIONS)}")

    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        return None

    approval.status = resolution
    approval.resolved_by = resolved_by
    approval.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(approval)
    return approval


async def list_approvals(
    db: AsyncSession,
    agent_id: str | None = None,
    status: str | None = "pending",
) -> list[Approval]:
    """List approvals, filtered by agent_id and/or status independently."""
    stmt = select(Approval)
    if agent_id is not None:
        stmt = stmt.where(Approval.agent_id == agent_id)
    if status is not None:
        stmt = stmt.where(Approval.status == status)
    stmt = stmt.order_by(Approval.id.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_approval(
    db: AsyncSession,
    approval_id: str,
) -> Approval | None:
    """Get a single approval by ID. Returns None if not found."""
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    return result.scalar_one_or_none()
