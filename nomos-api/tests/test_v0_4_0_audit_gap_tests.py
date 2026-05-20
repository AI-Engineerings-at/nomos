"""v0.4.0 R-phase regression tests — closes audit-B gaps F03, F09, F10.

These tests close gaps the QA audit identified after v0.2.0 but that
weren't part of the v0.2.1 / v0.3.0 hotfix/maintenance scopes:

- B-F03: GET /api/agents/{id}/audit/export path-traversal guard.
- B-F09: anchors.jsonl multi-agent interleave — verify endpoint must
  pick the RIGHT agent's last anchor when several agents have written
  into the same anchors.jsonl over time.
- B-F10: integrity-checkpoint re-run on a tampered chain — the second
  run's checkpoint MUST still report invalid (the previous design
  wrote the checkpoint into the chain itself, which made this case
  unpredictable; v0.3.0 M1 fixed the architecture, this test guards
  the contract).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nomos.core.events import EventType
from nomos.core.hash_chain import CHAIN_FILENAME, HashChain
from nomos_api.models import Agent


def _seed_chain(audit_dir: Path, agent_id: str, n: int = 3) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    chain = HashChain(storage_dir=audit_dir)
    for i in range(n):
        chain.append(
            event_type=EventType.AGENT_CREATED.value,
            agent_id=agent_id,
            data={"i": i},
        )


# -----------------------------------------------------------------------
# B-F03 — audit/export path-traversal guard.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_export_rejects_path_outside_agents_dir(
    client: AsyncClient, db_engine, tmp_path: Path, monkeypatch
) -> None:
    """If the Agent row's agents_dir points OUTSIDE settings.agents_dir
    (e.g. /etc, /var/log, or a sibling tenant) the export must 400, not
    silently leak the file. Closes audit B-F03 — previously the guard
    existed but had no test, so a future refactor could regress it
    undetected."""
    from nomos_api.config import settings as app_settings

    safe_base = tmp_path / "agents"
    safe_base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(app_settings, "agents_dir", safe_base)

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"esc-{uuid.uuid4().hex[:8]}"
    # agents_dir POINTS OUTSIDE safe_base (could be /etc, /var/log, ...)
    outside_dir = tmp_path / "outside" / agent_id
    outside_dir.mkdir(parents=True, exist_ok=True)

    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="t",
                role="external-secretary",
                company="x",
                email="u@x",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(outside_dir),
            )
        )
        await session.commit()

    resp = await client.get(f"/api/agents/{agent_id}/audit/export")
    assert resp.status_code == 400, (
        f"path-traversal export must be rejected, got status={resp.status_code} body={resp.text!r}"
    )


# -----------------------------------------------------------------------
# B-F09 — anchors.jsonl multi-agent interleave scan correctness.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_endpoint_picks_correct_agent_in_interleaved_anchors(
    client: AsyncClient, db_engine, tmp_path: Path, monkeypatch
) -> None:
    """anchors.jsonl is a global per-deployment file with one line per
    agent per anchor run. A verify call for agent B must pick the LAST
    line for agent B, ignoring intervening agent-A entries. Closes
    audit B-F09."""
    from nomos_api.config import settings as app_settings

    monkeypatch.setattr(app_settings, "agents_dir", tmp_path)
    anchors_path = tmp_path / "anchors" / "anchors.jsonl"
    monkeypatch.setattr(app_settings, "audit_anchors_path", anchors_path)
    anchors_path.parent.mkdir(parents=True, exist_ok=True)

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_a = f"a-{uuid.uuid4().hex[:8]}"
    agent_b = f"b-{uuid.uuid4().hex[:8]}"
    audit_a = tmp_path / agent_a / "audit"
    audit_b = tmp_path / agent_b / "audit"
    _seed_chain(audit_a, agent_a)
    _seed_chain(audit_b, agent_b)

    async with session_factory() as session:
        for agent_id, audit_dir in [(agent_a, audit_a), (agent_b, audit_b)]:
            session.add(
                Agent(
                    id=agent_id,
                    name=agent_id,
                    role="external-secretary",
                    company="x",
                    email="u@x",
                    risk_class="limited",
                    manifest_hash="x" * 64,
                    manifest_data={},
                    agents_dir=str(audit_dir.parent),
                )
            )
        await session.commit()

    # Write interleaved anchor lines for agent_a, then agent_b, then
    # agent_a AGAIN (newer A overrides older A, but B's lookup must
    # ignore A's lines entirely).
    head_b = json.loads((audit_b / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines()[-1])
    head_b_hash = head_b["hash"]
    with anchors_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "agent_id": agent_a,
                    "chain_length": 1,
                    "head_hash": "old_a_head",
                    "anchored_at": "2026-05-20T00:00:00Z",
                },
                sort_keys=True,
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "agent_id": agent_b,
                    "chain_length": 3,
                    "head_hash": head_b_hash,
                    "anchored_at": "2026-05-20T00:05:00Z",
                },
                sort_keys=True,
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "agent_id": agent_a,
                    "chain_length": 5,
                    "head_hash": "newer_a_head",
                    "anchored_at": "2026-05-20T00:10:00Z",
                },
                sort_keys=True,
            )
            + "\n"
        )

    resp = await client.get(f"/api/audit/verify/{agent_b}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["last_anchored_head_hash"] == head_b_hash, (
        f"verify must return B's last anchor head, got {body['last_anchored_head_hash']!r}"
    )
    assert body["head_matches_anchor"] is True


# -----------------------------------------------------------------------
# B-F10 — integrity-checkpoint re-run on a tampered chain.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_integrity_checkpoint_reports_invalid_on_rerun(db_engine, tmp_path: Path) -> None:
    """v0.3.0 (M1) moved the checkpoint OUT of the chain into a sibling
    file. Re-running the checkpoint on a chain that's still tampered
    MUST report invalid both times — there is no way for the checker
    to "self-clean" the verdict because the chain is read-only to it.
    Closes audit B-F10."""
    from nomos_api.worker.jobs.audit_retention import audit_integrity_checkpoint

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"chk-{uuid.uuid4().hex[:8]}"
    audit_dir = tmp_path / agent_id / "audit"
    _seed_chain(audit_dir, agent_id, n=3)

    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="chk",
                role="external-secretary",
                company="x",
                email="u@x",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(audit_dir.parent),
            )
        )
        await session.commit()

    # Tamper the first chain line (drop the HMAC field).
    chain_file = audit_dir / CHAIN_FILENAME
    lines = chain_file.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first.pop("hmac", None)
    lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    chain_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    checkpoints_path = tmp_path / "checkpoints.jsonl"
    counts_1 = await audit_integrity_checkpoint(
        None, session_factory=session_factory, checkpoints_path=checkpoints_path
    )
    assert counts_1["invalid"] == 1
    counts_2 = await audit_integrity_checkpoint(
        None, session_factory=session_factory, checkpoints_path=checkpoints_path
    )
    assert counts_2["invalid"] == 1, "second run on still-tampered chain MUST also report invalid"

    # checkpoints.jsonl must now have TWO records — both invalid.
    ckpt_lines = [ln for ln in checkpoints_path.read_text(encoding="utf-8").splitlines() if ln]
    assert len(ckpt_lines) == 2
    for raw in ckpt_lines:
        rec = json.loads(raw)
        assert rec["integrity_valid"] is False
        assert rec["errors_count"] >= 1
