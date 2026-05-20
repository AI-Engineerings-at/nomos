"""Phase-A2: external anchoring of the audit hash-chain head.

Every hour, for each agent, read the latest hash-chain entry and append
a line to the anchors file::

    {agent_id, chain_length, head_hash, head_hmac, head_signature,
     anchored_at}

The anchors file lives on a *separate* volume from the chains. In
production the operator mounts that volume on WORM-capable storage
(S3 Object Lock, Azure immutable blob, etc.) so even a full-write
attacker on the chain volume cannot silently rewrite the anchors.

Also writes an ``audit.chain.anchored`` event into the agent's own
chain to provide a forward marker that the anchor was taken.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos.core.events import EventType
from nomos.core.hash_chain import CHAIN_FILENAME, HashChain
from nomos_api.config import settings
from nomos_api.models import Agent

logger = logging.getLogger("nomos.worker.audit_anchor")


async def anchor_audit_heads(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
    anchors_path: Path | None = None,
) -> int:
    """Append an anchor record for every agent's chain head.

    Returns the number of agents anchored. Designed to be idempotent and
    safe to call from a cron schedule; each invocation produces exactly
    one anchor line per agent.
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()
    if anchors_path is None:
        anchors_path = settings.audit_anchors_path

    anchors_path.parent.mkdir(parents=True, exist_ok=True)

    anchored = 0
    async with session_factory() as session:
        result = await session.execute(select(Agent.id, Agent.agents_dir))
        agents = result.all()
    now_iso = datetime.now(timezone.utc).isoformat()

    for agent_id, agent_dir_raw in agents:
        try:
            agent_dir = Path(agent_dir_raw).resolve()
            chain_file = agent_dir / "audit" / CHAIN_FILENAME
            if not chain_file.exists():
                continue
            lines = [ln for ln in chain_file.read_text(encoding="utf-8").strip().split("\n") if ln]
            if not lines:
                continue
            last = json.loads(lines[-1])
            record = {
                "agent_id": agent_id,
                "chain_length": len(lines),
                "head_hash": last.get("hash"),
                "head_hmac": last.get("hmac"),
                "head_signature": last.get("signature"),
                "anchored_at": now_iso,
            }
            with anchors_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            # Forward marker in the chain itself — the next anchor run can
            # be cross-checked against the chain.
            chain = HashChain(storage_dir=agent_dir / "audit")
            chain.append(
                event_type=EventType.AUDIT_CHAIN_ANCHORED.value,
                agent_id=agent_id,
                data={"chain_length_before": len(lines), "anchored_at": now_iso},
            )
            anchored += 1
        except Exception:
            logger.exception("audit anchor failed for agent %s", agent_id)
    logger.info("anchored %d agent chains -> %s", anchored, anchors_path)
    return anchored
