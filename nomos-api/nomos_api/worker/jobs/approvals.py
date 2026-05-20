"""Approval Timeout Enforcement — expire pending approvals past their timeout.

Runs every 10 minutes. Pending approvals where ``requested_at +
timeout_minutes`` has passed are set to 'expired'.

M2d (0.3.0): the previous Python-loop implementation loaded every
pending approval into memory and re-computed the deadline per row in
Python. At any non-trivial volume that is an O(n) scan + per-row mutation
inside one transaction. Replaced with a single SQL ``UPDATE ... WHERE
status='pending' AND requested_at + (timeout_minutes * interval '1
minute') <= NOW()`` so Postgres handles the comparison natively. Audit
finding C-F8.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger("nomos.worker.approvals")


# Database-portable expression for "request has expired":
#   SQLite (tests in-memory):   `datetime(requested_at, '+' || timeout_minutes || ' minutes') <= datetime('now')`
#   PostgreSQL (production):    `requested_at + timeout_minutes * INTERVAL '1 minute' <= NOW()`
#
# We branch on the dialect via the bound engine name so the same job
# works under the SQLite test conftest and against real Postgres.
_POSTGRES_SQL = (
    "UPDATE approvals SET status = 'expired' "
    "WHERE status = 'pending' "
    "AND requested_at + (timeout_minutes * INTERVAL '1 minute') <= NOW()"
)
_SQLITE_SQL = (
    "UPDATE approvals SET status = 'expired' "
    "WHERE status = 'pending' "
    "AND datetime(requested_at, '+' || timeout_minutes || ' minutes') <= datetime('now')"
)


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
        Number of approvals expired (rowcount).
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    async with session_factory() as session:
        dialect = session.bind.dialect.name if session.bind else "postgresql"
        sql = _SQLITE_SQL if dialect == "sqlite" else _POSTGRES_SQL
        result = await session.execute(text(sql))
        expired_count = result.rowcount or 0
        await session.commit()

    if expired_count > 0:
        logger.info("Expired %d pending approvals (single UPDATE)", expired_count)

    return expired_count
