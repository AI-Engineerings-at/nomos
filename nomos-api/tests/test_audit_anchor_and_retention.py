"""Phase-A2 / A3 / A5 regression tests.

Covers the external chain-anchor cron, the periodic integrity-
checkpoint cron, the EU AI Act Art. 12 180-day retention floor at the
manifest validator, and the verify-endpoint anchor enrichment.
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


def _seed_agent_with_chain(db_engine, tmp_path: Path, agent_id: str) -> Path:
    """Helper: create an Agent DB row + a real chain.jsonl with one entry."""
    audit_dir = tmp_path / agent_id / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    chain = HashChain(storage_dir=audit_dir)
    chain.append(
        event_type=EventType.AGENT_CREATED.value,
        agent_id=agent_id,
        data={"seed": True},
    )
    return audit_dir


# -----------------------------------------------------------------------
# Phase-A3 — manifest 180-day retention floor (EU AI Act Art. 12 min).
# -----------------------------------------------------------------------


def test_manifest_rejects_audit_retention_below_180_days() -> None:
    from pydantic import ValidationError

    from nomos.core.manifest import GovernanceConfig

    GovernanceConfig(audit_retention_days=180)  # at the floor — OK
    GovernanceConfig(audit_retention_days=365)  # default — OK
    with pytest.raises(ValidationError):
        GovernanceConfig(audit_retention_days=179)  # one day below — REJECT
    with pytest.raises(ValidationError):
        GovernanceConfig(audit_retention_days=30)  # well below — REJECT


# -----------------------------------------------------------------------
# Phase-A2 — anchor_audit_heads writes one line per agent to anchors.jsonl.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_anchor_audit_heads_writes_external_anchor(db_engine, tmp_path: Path) -> None:
    from nomos_api.worker.jobs.audit_anchor import anchor_audit_heads

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"a-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_agent_with_chain(db_engine, tmp_path, agent_id)

    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="anchor-test",
                role="external-secretary",
                company="acme",
                email="u@acme",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(audit_dir.parent),
            )
        )
        await session.commit()

    anchors_path = tmp_path / "anchors" / "anchors.jsonl"
    anchored = await anchor_audit_heads(
        None,
        session_factory=session_factory,
        anchors_path=anchors_path,
    )
    assert anchored == 1
    assert anchors_path.exists()
    lines = [ln for ln in anchors_path.read_text(encoding="utf-8").splitlines() if ln]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["agent_id"] == agent_id
    assert rec["chain_length"] == 1
    assert rec["head_hash"] and len(rec["head_hash"]) == 64
    assert rec["head_hmac"] and len(rec["head_hmac"]) == 64
    assert rec["head_signature"] and len(rec["head_signature"]) == 128
    assert "anchored_at" in rec

    # M1 (0.3.0): the anchor cron NO LONGER writes a forward marker
    # back into the chain. The chain stays at exactly the entries the
    # caller appended (1 in this fixture); the anchor file alone is
    # the durable record. See LEARNINGS L040.
    chain_lines = [ln for ln in (audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines() if ln]
    assert len(chain_lines) == 1, "anchor cron must not append to the chain in 0.3.0+"


# -----------------------------------------------------------------------
# Phase-A3 — audit_integrity_checkpoint runs verify + writes checkpoint.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_integrity_checkpoint_writes_checkpoint(db_engine, tmp_path: Path) -> None:
    from nomos_api.worker.jobs.audit_retention import audit_integrity_checkpoint

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"chk-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_agent_with_chain(db_engine, tmp_path, agent_id)

    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="chk",
                role="external-secretary",
                company="acme",
                email="u@acme",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(audit_dir.parent),
            )
        )
        await session.commit()

    checkpoints_path = tmp_path / "anchors" / "checkpoints.jsonl"
    counts = await audit_integrity_checkpoint(
        None,
        session_factory=session_factory,
        checkpoints_path=checkpoints_path,
    )
    assert counts == {"checked": 1, "valid": 1, "invalid": 0}

    # M1 (0.3.0): the checkpoint is written to a SIBLING file, not the
    # chain. The chain stays at the original 1 entry.
    chain_lines = [ln for ln in (audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines() if ln]
    assert len(chain_lines) == 1, "checkpoint cron must not append to the chain in 0.3.0+"

    assert checkpoints_path.exists()
    ckpt_lines = [ln for ln in checkpoints_path.read_text(encoding="utf-8").splitlines() if ln]
    assert len(ckpt_lines) == 1
    rec = json.loads(ckpt_lines[0])
    assert rec["agent_id"] == agent_id
    assert rec["integrity_valid"] is True
    assert rec["entries_checked"] == 1
    assert rec["errors_count"] == 0
    assert rec["art12_min_retention_days"] == 180
    assert "checkpoint_at" in rec


@pytest.mark.asyncio
async def test_audit_integrity_checkpoint_flags_tampered_chain(db_engine, tmp_path: Path) -> None:
    from nomos_api.worker.jobs.audit_retention import audit_integrity_checkpoint

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"tmp-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_agent_with_chain(db_engine, tmp_path, agent_id)

    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="t",
                role="external-secretary",
                company="acme",
                email="u@acme",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(audit_dir.parent),
            )
        )
        await session.commit()

    # Tamper: drop the HMAC field — verify_chain MUST flag invalid.
    chain_file = audit_dir / CHAIN_FILENAME
    obj = json.loads(chain_file.read_text(encoding="utf-8").strip())
    obj.pop("hmac", None)
    chain_file.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")

    checkpoints_path = tmp_path / "anchors" / "checkpoints.jsonl"
    counts = await audit_integrity_checkpoint(
        None,
        session_factory=session_factory,
        checkpoints_path=checkpoints_path,
    )
    assert counts["invalid"] == 1, f"tampered chain must be flagged invalid: {counts}"
    # And the invalid result IS reflected in the checkpoint record.
    ckpt = json.loads(checkpoints_path.read_text(encoding="utf-8").strip())
    assert ckpt["integrity_valid"] is False
    assert ckpt["errors_count"] >= 1


# -----------------------------------------------------------------------
# Phase-A5 — verify endpoint returns anchor info.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_endpoint_reports_anchor_match(
    client: AsyncClient, db_engine, tmp_path: Path, monkeypatch
) -> None:
    """Drive: anchor the chain, then GET /audit/verify and assert the
    anchor fields are populated AND head_matches_anchor=True."""
    from nomos_api.config import settings as app_settings
    from nomos_api.worker.jobs.audit_anchor import anchor_audit_heads

    monkeypatch.setattr(app_settings, "agents_dir", tmp_path)
    anchors_path = tmp_path / "anchors" / "anchors.jsonl"
    monkeypatch.setattr(app_settings, "audit_anchors_path", anchors_path)

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"v-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_agent_with_chain(db_engine, tmp_path, agent_id)
    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="v",
                role="external-secretary",
                company="acme",
                email="u@acme",
                risk_class="limited",
                manifest_hash="x" * 64,
                manifest_data={},
                agents_dir=str(audit_dir.parent),
            )
        )
        await session.commit()

    # Take an anchor.
    await anchor_audit_heads(None, session_factory=session_factory, anchors_path=anchors_path)

    resp = await client.get(f"/api/audit/verify/{agent_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["valid"] is True
    assert body["last_anchored_at"], "verify must return last_anchored_at after an anchor run"
    assert body["last_anchored_head_hash"], "verify must return last_anchored_head_hash"
    # M1 (0.3.0): the anchor cron NO LONGER appends a marker into the
    # chain — anchored head and current head are equal at this moment
    # (no further chain activity since the anchor). head_matches_anchor
    # MUST be True now (correct quiescent-state semantics).
    assert body["head_matches_anchor"] is True
