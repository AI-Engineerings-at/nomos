"""Audit event writer — shared by all routers that append to the hash chain."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.models import Agent, AuditLog
from nomos.core.events import EventType
from nomos.core.hash_chain import HashChain


async def write_audit_event(
    db: AsyncSession,
    agent: Agent,
    agent_id: str,
    event_type: EventType,
    data: dict,
) -> None:
    """Write an event to the on-disk hash chain and persist it to the DB."""
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        return
    audit_dir = agent_dir / "audit"
    if not audit_dir.exists():
        return
    chain = HashChain(storage_dir=audit_dir)
    entry = chain.append(
        event_type=event_type,
        agent_id=agent_id,
        data=data,
    )
    audit_log = AuditLog(
        agent_id=entry.agent_id,
        sequence=entry.sequence,
        event_type=entry.event_type,
        data=entry.data,
        chain_hash=entry.hash,
        timestamp=entry.timestamp,
    )
    db.add(audit_log)
    await db.commit()
