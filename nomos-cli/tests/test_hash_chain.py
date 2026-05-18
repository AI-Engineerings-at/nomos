"""Tests for NomOS Hash Chain — tamper-evident audit trail."""

from __future__ import annotations

import hashlib
import hmac as _hmac
import json
from pathlib import Path

from nomos.core.hash_chain import (
    _HMAC_ENV_VAR,
    HashChainEntry,
    HashChain,
    verify_chain,
)


class TestHashChainEntry:
    def test_entry_has_required_fields(self) -> None:
        entry = HashChainEntry(
            sequence=0,
            timestamp="2026-03-23T12:00:00Z",
            event_type="agent.created",
            agent_id="mani-v1",
            data={"name": "Mani Ruf"},
            previous_hash="0" * 64,
        )
        assert entry.sequence == 0
        assert entry.event_type == "agent.created"
        assert entry.agent_id == "mani-v1"
        assert len(entry.hash) == 64

    def test_entry_hash_is_deterministic(self) -> None:
        kwargs = dict(
            sequence=0,
            timestamp="2026-03-23T12:00:00Z",
            event_type="agent.created",
            agent_id="mani-v1",
            data={"name": "Mani Ruf"},
            previous_hash="0" * 64,
        )
        e1 = HashChainEntry(**kwargs)
        e2 = HashChainEntry(**kwargs)
        assert e1.hash == e2.hash

    def test_entry_hash_changes_with_data(self) -> None:
        base = dict(
            sequence=0,
            timestamp="2026-03-23T12:00:00Z",
            event_type="agent.created",
            agent_id="mani-v1",
            previous_hash="0" * 64,
        )
        e1 = HashChainEntry(**base, data={"name": "Mani"})
        e2 = HashChainEntry(**base, data={"name": "Other"})
        assert e1.hash != e2.hash


class TestHashChain:
    def test_new_chain_is_empty(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        assert len(chain) == 0

    def test_append_creates_entry(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        entry = chain.append(
            event_type="agent.created",
            agent_id="mani-v1",
            data={"name": "Mani Ruf"},
        )
        assert entry.sequence == 0
        assert entry.previous_hash == "0" * 64
        assert len(chain) == 1

    def test_chain_links_entries(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        e1 = chain.append(event_type="agent.created", agent_id="mani-v1", data={})
        e2 = chain.append(event_type="agent.deployed", agent_id="mani-v1", data={})
        assert e2.previous_hash == e1.hash
        assert e2.sequence == 1

    def test_chain_persists_to_jsonl(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="mani-v1", data={"x": 1})
        chain.append(event_type="agent.deployed", agent_id="mani-v1", data={"x": 2})
        chain_file = tmp_path / "chain.jsonl"
        assert chain_file.exists()
        lines = chain_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["sequence"] == 0
        assert first["event_type"] == "agent.created"

    def test_chain_loads_from_existing_file(self, tmp_path: Path) -> None:
        chain1 = HashChain(storage_dir=tmp_path)
        chain1.append(event_type="agent.created", agent_id="test", data={})
        chain1.append(event_type="agent.deployed", agent_id="test", data={})
        chain2 = HashChain(storage_dir=tmp_path)
        assert len(chain2) == 2


class TestVerifyChain:
    def test_valid_chain_passes(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="test", data={})
        chain.append(event_type="agent.deployed", agent_id="test", data={})
        chain.append(event_type="compliance.passed", agent_id="test", data={})
        result = verify_chain(tmp_path)
        assert result.valid is True
        assert result.entries_checked == 3
        assert len(result.errors) == 0

    def test_tampered_chain_fails(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="test", data={})
        chain.append(event_type="agent.deployed", agent_id="test", data={})
        chain_file = tmp_path / "chain.jsonl"
        lines = chain_file.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(lines[0])
        entry["data"] = {"tampered": True}
        lines[0] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        chain_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = verify_chain(tmp_path)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_empty_chain_is_valid(self, tmp_path: Path) -> None:
        result = verify_chain(tmp_path)
        assert result.valid is True
        assert result.entries_checked == 0

    def test_corrupt_jsonl_line_detected(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="test", data={})
        chain_file = tmp_path / "chain.jsonl"
        with chain_file.open("a", encoding="utf-8") as f:
            f.write("THIS IS NOT JSON\n")
        result = verify_chain(tmp_path)
        assert result.valid is False
        assert any("corrupt" in e.lower() or "parse" in e.lower() for e in result.errors)


class TestHmacAnchoring:
    """M3: HMAC anchoring makes a consistent rewrite detectable."""

    def test_entry_has_hmac(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        entry = chain.append(event_type="agent.created", agent_id="a", data={})
        assert len(entry.hmac) == 64
        line = json.loads((tmp_path / "chain.jsonl").read_text().strip())
        assert "hmac" in line and line["hmac"] == entry.hmac

    def test_consistent_rewrite_without_key_is_detected(self, tmp_path: Path) -> None:
        """Rewrite data AND recompute hash (consistent) — HMAC still fails."""
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="test", data={"v": 1})
        chain_file = tmp_path / "chain.jsonl"
        raw = json.loads(chain_file.read_text().strip())

        # Attacker forges content and recomputes the (public) SHA-256 hash,
        # but cannot compute a valid HMAC without the secret key.
        raw["data"] = {"v": "tampered"}
        canonical = json.dumps(
            {
                "sequence": raw["sequence"],
                "timestamp": raw["timestamp"],
                "event_type": raw["event_type"],
                "agent_id": raw["agent_id"],
                "data": raw["data"],
                "previous_hash": raw["previous_hash"],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        raw["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        # Forge HMAC with the WRONG key.
        raw["hmac"] = _hmac.new(b"attacker-key", raw["hash"].encode(), hashlib.sha256).hexdigest()
        chain_file.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")

        result = verify_chain(tmp_path)
        assert result.valid is False
        assert any("HMAC" in e for e in result.errors)

    def test_valid_chain_with_hmac_passes(self, tmp_path: Path) -> None:
        chain = HashChain(storage_dir=tmp_path)
        chain.append(event_type="agent.created", agent_id="test", data={})
        chain.append(event_type="agent.deployed", agent_id="test", data={})
        result = verify_chain(tmp_path)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_legacy_entry_without_hmac_still_verifies(self, tmp_path: Path) -> None:
        """Backward compat: pre-HMAC JSONL (no hmac field) still validates."""
        chain = HashChain(storage_dir=tmp_path)
        e = chain.append(event_type="agent.created", agent_id="test", data={"x": 1})
        chain_file = tmp_path / "chain.jsonl"
        raw = json.loads(chain_file.read_text().strip())
        del raw["hmac"]  # simulate a legacy entry
        chain_file.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
        result = verify_chain(tmp_path)
        assert result.valid is True
        assert e.hash == raw["hash"]

    def test_hmac_key_is_env_injectable(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv(_HMAC_ENV_VAR, "a-different-production-key-value-1234")
        chain = HashChain(storage_dir=tmp_path)
        entry = chain.append(event_type="agent.created", agent_id="test", data={})
        expected = _hmac.new(
            b"a-different-production-key-value-1234", entry.hash.encode(), hashlib.sha256
        ).hexdigest()
        assert entry.hmac == expected
