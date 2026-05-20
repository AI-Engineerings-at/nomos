"""Phase-A2 (+ M1, 0.3.0): external anchoring of the audit hash-chain head.

Every hour, for each agent, read the latest hash-chain entry and append
a line to the anchors file::

    {agent_id, chain_length, head_hash, head_hmac, head_signature,
     merkle_tree_size, merkle_root_hash, anchored_at}

The anchors file lives on a *separate* volume from the chains. In
production the operator mounts that volume on WORM-capable storage
(S3 Object Lock, Azure immutable blob, etc.) so even a full-write
attacker on the chain volume cannot silently rewrite the anchors.

M1 (0.3.0): the forward-marker ``audit.chain.anchored`` event is NO
LONGER written back into the chain — see LEARNINGS L040 and audit
finding C-F3. Writing the marker INTO the chain it just anchored
meant every anchor described a head_hash that became stale one entry
later; external verifiers had to chase the marker to explain the
delta. The anchor file alone is the durable record now; the chain
stays for genuine agent events.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos.core.hash_chain import CHAIN_FILENAME
from nomos.core.merkle import compute_tree_root
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
                logger.warning(
                    "audit anchor skipped: chain file missing for agent=%s path=%s",
                    agent_id,
                    chain_file,
                )
                continue
            lines = [ln for ln in chain_file.read_text(encoding="utf-8").strip().split("\n") if ln]
            if not lines:
                continue
            last = json.loads(lines[-1])
            # Phase-B1: also anchor the Merkle root of the tree at the
            # time of capture, so external verifiers can later validate
            # an inclusion proof against a known-good historical root.
            tree_size, root_bytes = compute_tree_root(agent_dir / "audit")
            record = {
                "agent_id": agent_id,
                "chain_length": len(lines),
                "head_hash": last.get("hash"),
                "head_hmac": last.get("hmac"),
                "head_signature": last.get("signature"),
                "merkle_tree_size": tree_size,
                "merkle_root_hash": root_bytes.hex(),
                "anchored_at": now_iso,
            }
            with anchors_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            anchored += 1
        except Exception:
            # M4-style: log enough context to diagnose without re-running.
            logger.exception(
                "audit anchor failed for agent=%s agents_dir=%s",
                agent_id,
                agent_dir_raw,
            )
    logger.info("anchored %d agent chains -> %s", anchored, anchors_path)
    return anchored
