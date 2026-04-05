"""Approval Timeout Enforcement — expire pending approvals past their timeout.

Runs every 10 minutes. Pending approvals where requested_at + timeout_minutes
has passed are set to 'expired'.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos_api.models import Approval

logger = logging.getLogger("nomos.worker.approvals")


async def expire_approvals(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
) -> int:
    """Expire pending approvals that have timed out.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        session_factory: Override for testing. Production uses module-level factory.

    Returns:
        Number of approvals expired.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    now = datetime.now(timezone.utc)
    expired_count = 0

    async with session_factory() as session:
        result = await session.execute(select(Approval).where(Approval.status == "pending"))
        pending = result.scalars().all()

        for approval in pending:
            requested = approval.requested_at
            # Ensure timezone-aware comparison
            if requested.tzinfo is None:
                requested = requested.replace(tzinfo=timezone.utc)

            expiry_time = requested + timedelta(minutes=approval.timeout_minutes)
            if expiry_time <= now:
                approval.status = "expired"
                expired_count += 1

        await session.commit()

    if expired_count > 0:
        logger.info("Expired %d pending approvals", expired_count)

    return expired_count
