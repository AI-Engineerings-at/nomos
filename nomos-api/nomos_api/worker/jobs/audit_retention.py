"""Phase-A3 (+ M1, 0.3.0): periodic audit-chain integrity checkpoint.

EU AI Act Art. 12 requires automatic logging over the system lifetime
with a minimum 6-month retention. The audit hash chain is append-only
by design (each entry binds its predecessor via ``previous_hash``);
physically pruning entries would break that cryptographic continuity.

This job therefore does NOT delete chain entries. Instead it runs a
periodic INTEGRITY CHECKPOINT for every agent's chain:

1. Re-verify the chain (SHA-256 + HMAC + Ed25519 signature).
2. Record the result as one JSONL line in a SIBLING file
   ``checkpoints.jsonl`` (next to ``anchors.jsonl`` on the same
   WORM-ready volume). Previous releases wrote the checkpoint INTO
   the chain itself — see LEARNINGS L040 and audit finding C-F16:
   an integrity-checker that mutates the chain it just verified can
   never describe a quiescent state. From 0.3.0 the chain stays
   pristine; checkpoints live alongside the anchors.
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

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from nomos.core.hash_chain import verify_chain
from nomos_api.config import settings
from nomos_api.models import Agent

logger = logging.getLogger("nomos.worker.audit_retention")

# Article 12 statutory minimum.
ART12_MIN_RETENTION_DAYS = 180


async def audit_integrity_checkpoint(
    ctx: dict[str, Any] | None,
    *,
    session_factory: async_sessionmaker | None = None,
    checkpoints_path: Path | None = None,
) -> dict[str, int]:
    """Run an integrity checkpoint on every agent's chain.

    Returns ``{checked, valid, invalid}`` for monitoring.

    Each invocation appends one JSON line per agent to
    ``settings.audit_checkpoints_path`` (override via
    ``checkpoints_path`` for tests).
    """
    if session_factory is None:
        from nomos_api.worker.main import get_session_factory

        session_factory = get_session_factory()
    if checkpoints_path is None:
        checkpoints_path = settings.audit_checkpoints_path

    checkpoints_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    async with session_factory() as session:
        result = await session.execute(select(Agent.id, Agent.agents_dir))
        agents = result.all()

    counts = {"checked": 0, "valid": 0, "invalid": 0}
    for agent_id, agent_dir_raw in agents:
        try:
            agent_dir = Path(agent_dir_raw).resolve()
            audit_dir = agent_dir / "audit"
            if not audit_dir.exists():
                logger.warning(
                    "audit integrity checkpoint skipped: audit dir missing agent=%s audit_dir=%s",
                    agent_id,
                    audit_dir,
                )
                continue
            res = verify_chain(audit_dir)
            counts["checked"] += 1
            if res.valid:
                counts["valid"] += 1
            else:
                counts["invalid"] += 1
                logger.error(
                    "audit chain integrity FAILED agent=%s entries_checked=%d errors=%d first_error=%r",
                    agent_id,
                    res.entries_checked,
                    len(res.errors),
                    res.errors[0] if res.errors else None,
                )
            # M1 (0.3.0): write checkpoint to sibling JSONL — NOT the
            # chain. Schema mirrors anchors.jsonl for symmetry; first 5
            # error messages kept so the line stays small.
            record = {
                "agent_id": agent_id,
                "checkpoint_at": now_iso,
                "integrity_valid": res.valid,
                "entries_checked": res.entries_checked,
                "errors_count": len(res.errors),
                "errors_preview": res.errors[:5],
                "art12_min_retention_days": ART12_MIN_RETENTION_DAYS,
            }
            with checkpoints_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except Exception:
            logger.exception(
                "audit integrity checkpoint failed agent=%s agents_dir=%s",
                agent_id,
                agent_dir_raw,
            )
    logger.info(
        "audit integrity checkpoint: checked=%d valid=%d invalid=%d -> %s",
        counts["checked"],
        counts["valid"],
        counts["invalid"],
        checkpoints_path,
    )
    return counts
