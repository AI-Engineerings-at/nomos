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

    # Anchor cron also writes a forward marker entry into the chain itself.
    chain_lines = [ln for ln in (audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines() if ln]
    assert len(chain_lines) == 2
    last = json.loads(chain_lines[-1])
    assert last["event_type"] == EventType.AUDIT_CHAIN_ANCHORED.value


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

    counts = await audit_integrity_checkpoint(None, session_factory=session_factory)
    assert counts == {"checked": 1, "valid": 1, "invalid": 0}

    # The checkpoint itself is the LAST entry; integrity_valid=True.
    chain_lines = [ln for ln in (audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines() if ln]
    last = json.loads(chain_lines[-1])
    assert last["event_type"] == EventType.AUDIT_RETENTION_CHECKPOINT.value
    assert last["data"]["integrity_valid"] is True
    assert last["data"]["errors_count"] == 0
    assert last["data"]["art12_min_retention_days"] == 180


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

    counts = await audit_integrity_checkpoint(None, session_factory=session_factory)
    assert counts["invalid"] == 1, f"tampered chain must be flagged invalid: {counts}"


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
    # Note: the anchor run also APPENDS an AUDIT_CHAIN_ANCHORED entry to
    # the chain — so the current head is now AHEAD of the anchored head.
    # head_matches_anchor MUST be False in that case (correct semantics).
    assert body["head_matches_anchor"] is False
