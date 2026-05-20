"""Phase-A3: periodic audit-chain integrity checkpoint.

EU AI Act Art. 12 requires automatic logging over the system lifetime
with a minimum 6-month retention. The audit hash chain is append-only
by design (each entry binds its predecessor via ``previous_hash``);
physically pruning entries would break that cryptographic continuity.

This job therefore does NOT delete chain entries. Instead it runs a
periodic INTEGRITY CHECKPOINT for every agent's chain:

1. Re-verify the chain (SHA-256 + HMAC + Ed25519 signature).
2. Record the result as an ``audit.retention.checkpoint`` event inside
   the chain itself, with chain length and any integrity errors.
3. Log a WARNING / ERROR if integrity fails — surfaces tampering
   between scheduled checks.

A separate manifest-level validator (``manifest_validator``) enforces
the Art. 12 minimum 6-month retention floor on the customer-configured
``manifest.governance.audit_retention_days``.

DSGVO right-to-be-forgotten (Art. 17) is handled by the dedicated
``services.forget`` path, NOT here — that path operates on the
``agent_memory`` table, not the audit chain.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos.core.events import EventType
from nomos.core.hash_chain import HashChain, verify_chain
from nomos_api.models import Agent

logger = logging.getLogger("nomos.worker.audit_retention")

# Article 12 statutory minimum.
ART12_MIN_RETENTION_DAYS = 180


async def audit_integrity_checkpoint(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
) -> dict[str, int]:
    """Run an integrity checkpoint on every agent's chain.

    Returns ``{checked, valid, invalid}`` for monitoring.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()

    from pathlib import Path

    async with session_factory() as session:
        result = await session.execute(select(Agent.id, Agent.agents_dir))
        agents = result.all()

    counts = {"checked": 0, "valid": 0, "invalid": 0}
    for agent_id, agent_dir_raw in agents:
        try:
            agent_dir = Path(agent_dir_raw).resolve()
            audit_dir = agent_dir / "audit"
            if not audit_dir.exists():
                continue
            res = verify_chain(audit_dir)
            counts["checked"] += 1
            if res.valid:
                counts["valid"] += 1
            else:
                counts["invalid"] += 1
                logger.error(
                    "audit chain integrity FAILED for %s: %d errors",
                    agent_id,
                    len(res.errors),
                )
            # Always write a checkpoint entry — even on failure, so the
            # checkpoint itself becomes an auditable record of the check.
            chain = HashChain(storage_dir=audit_dir)
            chain.append(
                event_type=EventType.AUDIT_RETENTION_CHECKPOINT.value,
                agent_id=agent_id,
                data={
                    "integrity_valid": res.valid,
                    "entries_checked": res.entries_checked,
                    "errors_count": len(res.errors),
                    # First few error messages only — keep the entry small.
                    "errors_preview": res.errors[:5],
                    "art12_min_retention_days": ART12_MIN_RETENTION_DAYS,
                },
            )
        except Exception:
            logger.exception("audit integrity checkpoint failed for agent %s", agent_id)
    logger.info(
        "audit integrity checkpoint: checked=%d valid=%d invalid=%d",
        counts["checked"],
        counts["valid"],
        counts["invalid"],
    )
    return counts
