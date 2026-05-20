"""Phase-B1 regression tests — embedded Merkle transparency log.

Covers: RFC 6962 leaf/internal hashing, signed tree head (STH)
round-trip, inclusion-proof round-trip via API, anchor record now
carries merkle_root_hash, third-party verification path.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nomos.core.events import EventType
from nomos.core.hash_chain import CHAIN_FILENAME, HashChain
from nomos.core.merkle import (
    compute_tree_root,
    inclusion_proof,
    signed_tree_head,
    verify_inclusion_proof,
    verify_signed_tree_head,
)
from nomos_api.models import Agent


def _seed_chain(tmp_path: Path, agent_id: str, n_entries: int = 5) -> Path:
    audit_dir = tmp_path / agent_id / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    chain = HashChain(storage_dir=audit_dir)
    for i in range(n_entries):
        chain.append(
            event_type=EventType.AGENT_CREATED.value,
            agent_id=agent_id,
            data={"i": i},
        )
    return audit_dir


# -----------------------------------------------------------------------
# Pure-function Merkle tree tests
# -----------------------------------------------------------------------


def test_empty_tree_size_zero(tmp_path: Path) -> None:
    audit_dir = tmp_path / "empty" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    tree_size, _ = compute_tree_root(audit_dir)
    assert tree_size == 0


def test_single_leaf_root_matches_rfc6962(tmp_path: Path) -> None:
    audit_dir = _seed_chain(tmp_path, "single", n_entries=1)
    tree_size, root = compute_tree_root(audit_dir)
    assert tree_size == 1
    chain_line = json.loads((audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").strip())
    expected = hashlib.sha256(b"\x00" + chain_line["hash"].encode("utf-8")).digest()
    assert root == expected, "single-leaf Merkle root == SHA-256(0x00||leaf)"


def test_inclusion_proof_roundtrip_for_every_leaf(tmp_path: Path) -> None:
    """An inclusion proof for any leaf must reconstruct the root."""
    audit_dir = _seed_chain(tmp_path, "multi", n_entries=11)  # non-power-of-2
    chain_lines = (audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines()
    tree_size_expected, root_expected = compute_tree_root(audit_dir)
    for i, raw in enumerate(chain_lines):
        leaf_hex = json.loads(raw)["hash"]
        proof = inclusion_proof(audit_dir, leaf_index=i)
        assert proof["tree_size"] == tree_size_expected
        assert proof["root_hash"] == root_expected.hex()
        ok = verify_inclusion_proof(
            leaf_data=leaf_hex.encode("utf-8"),
            leaf_index=i,
            tree_size=proof["tree_size"],
            audit_path_hex=proof["audit_path"],
            root_hash_hex=proof["root_hash"],
        )
        assert ok, f"inclusion proof for leaf {i} failed to verify"


def test_inclusion_proof_rejects_wrong_leaf(tmp_path: Path) -> None:
    audit_dir = _seed_chain(tmp_path, "tamp", n_entries=7)
    proof = inclusion_proof(audit_dir, leaf_index=3)
    bad = verify_inclusion_proof(
        leaf_data=b"x" * 64,  # arbitrary wrong leaf data
        leaf_index=3,
        tree_size=proof["tree_size"],
        audit_path_hex=proof["audit_path"],
        root_hash_hex=proof["root_hash"],
    )
    assert bad is False


def test_signed_tree_head_roundtrip(tmp_path: Path) -> None:
    audit_dir = _seed_chain(tmp_path, "sth", n_entries=4)
    sth = signed_tree_head(audit_dir, origin="nomos-audit/sth")
    assert verify_signed_tree_head(sth) is True
    # Tamper: change the root, signature must reject.
    sth_bad = dict(sth)
    sth_bad["root_hash"] = "0" * 64
    assert verify_signed_tree_head(sth_bad) is False


def test_inclusion_proof_out_of_range_raises(tmp_path: Path) -> None:
    audit_dir = _seed_chain(tmp_path, "oor", n_entries=3)
    with pytest.raises(IndexError):
        inclusion_proof(audit_dir, leaf_index=99)


# -----------------------------------------------------------------------
# API endpoints
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_signed_tree_head_endpoint(client: AsyncClient, db_engine, tmp_path: Path, monkeypatch) -> None:
    from nomos_api.config import settings as app_settings

    monkeypatch.setattr(app_settings, "agents_dir", tmp_path)
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"sth-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_chain(tmp_path, agent_id, n_entries=3)
    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="x",
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
    resp = await client.get(f"/api/agents/{agent_id}/audit/sth")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tree_size"] == 3
    assert len(body["root_hash"]) == 64
    assert len(body["signature"]) == 128
    # Verify via the pure-function path with the same key set in conftest.
    sth_for_verify = {
        "origin": body["origin"],
        "tree_size": body["tree_size"],
        "root_hash": body["root_hash"],
        "timestamp": body["timestamp"],
        "signature": body["signature"],
    }
    assert verify_signed_tree_head(sth_for_verify) is True


@pytest.mark.asyncio
async def test_api_inclusion_proof_endpoint_roundtrip(
    client: AsyncClient, db_engine, tmp_path: Path, monkeypatch
) -> None:
    from nomos_api.config import settings as app_settings

    monkeypatch.setattr(app_settings, "agents_dir", tmp_path)
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"ip-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_chain(tmp_path, agent_id, n_entries=6)
    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="x",
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

    leaf_hex = json.loads((audit_dir / CHAIN_FILENAME).read_text(encoding="utf-8").splitlines()[2])["hash"]
    resp = await client.get(f"/api/agents/{agent_id}/audit/proof/2")
    assert resp.status_code == 200, resp.text
    proof = resp.json()
    assert proof["leaf_index"] == 2
    assert proof["tree_size"] == 6
    ok = verify_inclusion_proof(
        leaf_data=leaf_hex.encode("utf-8"),
        leaf_index=2,
        tree_size=proof["tree_size"],
        audit_path_hex=proof["audit_path"],
        root_hash_hex=proof["root_hash"],
    )
    assert ok is True


@pytest.mark.asyncio
async def test_api_inclusion_proof_out_of_range_404(
    client: AsyncClient, db_engine, tmp_path: Path, monkeypatch
) -> None:
    from nomos_api.config import settings as app_settings

    monkeypatch.setattr(app_settings, "agents_dir", tmp_path)
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"oor-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_chain(tmp_path, agent_id, n_entries=2)
    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="x",
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
    resp = await client.get(f"/api/agents/{agent_id}/audit/proof/99")
    assert resp.status_code == 404


# -----------------------------------------------------------------------
# Anchor cron now stores merkle_root_hash too.
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_anchor_records_carry_merkle_root(db_engine, tmp_path: Path) -> None:
    from nomos_api.worker.jobs.audit_anchor import anchor_audit_heads

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    agent_id = f"mr-{uuid.uuid4().hex[:8]}"
    audit_dir = _seed_chain(tmp_path, agent_id, n_entries=4)
    async with session_factory() as session:
        session.add(
            Agent(
                id=agent_id,
                name="x",
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
    await anchor_audit_heads(None, session_factory=session_factory, anchors_path=anchors_path)
    rec = json.loads(anchors_path.read_text(encoding="utf-8").strip())
    assert "merkle_tree_size" in rec
    assert "merkle_root_hash" in rec
    assert rec["merkle_tree_size"] == 4
    assert len(rec["merkle_root_hash"]) == 64
