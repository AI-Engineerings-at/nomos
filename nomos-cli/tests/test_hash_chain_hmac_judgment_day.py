"""Regression tests for the post-judgment-day hash-chain hardening.

C1: _hmac_key() fails closed when NOMOS_HASHCHAIN_HMAC_KEY is missing/short.
H4: verify_chain rejects entries that have NO `hmac` field (legacy bypass closed).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nomos.core.hash_chain import (
    CHAIN_FILENAME,
    HashChain,
    HashChainKeyMissing,
    _hmac_key,
    verify_chain,
)


def test_hmac_key_fails_closed_without_env(monkeypatch) -> None:
    monkeypatch.delenv("NOMOS_HASHCHAIN_HMAC_KEY", raising=False)
    with pytest.raises(HashChainKeyMissing):
        _hmac_key()


def test_hmac_key_fails_closed_with_short_env(monkeypatch) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", "too-short")  # < 32 bytes
    with pytest.raises(HashChainKeyMissing):
        _hmac_key()


def test_verify_chain_rejects_entries_without_hmac_field(tmp_path: Path) -> None:
    """Drop-the-hmac-field attack must NOT verify.

    Pre-fix: verify_chain accepted entries missing the hmac field as
    "legacy" — an attacker could rewrite the chain and simply omit hmac
    to defeat the anchor. Now: missing hmac = invalid.
    """
    chain = HashChain(tmp_path)
    chain.append("agent_started", "agent-x", {"by": "test"})
    chain.append("agent_stopped", "agent-x", {"by": "test"})

    # Strip the hmac field from every line — the attack scenario.
    p = tmp_path / CHAIN_FILENAME
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    stripped = []
    for ln in lines:
        obj = json.loads(ln)
        obj.pop("hmac", None)
        stripped.append(json.dumps(obj, sort_keys=True, separators=(",", ":")))
    p.write_text("\n".join(stripped) + "\n", encoding="utf-8")

    result = verify_chain(tmp_path)
    assert result.valid is False, "missing-hmac attack must fail verify_chain"
    assert any("missing HMAC" in e for e in result.errors), f"expected missing-HMAC error, got {result.errors}"


def test_verify_chain_rejects_rewrite_without_key(tmp_path: Path, monkeypatch) -> None:
    """Even a self-consistent rewrite must fail when the attacker uses a
    different HMAC key. Demonstrates that the HMAC is the actual anchor."""
    chain = HashChain(tmp_path)
    chain.append("e1", "a", {"v": 1})
    chain.append("e2", "a", {"v": 2})

    # Attacker has the chain file but NOT the production HMAC key. Switch
    # to a different (still >=32-byte) key and re-write the file from
    # scratch using HashChain. This produces a SHA-256-consistent chain
    # whose HMACs are bound to the attacker's key, not the real one.
    p = tmp_path / CHAIN_FILENAME
    p.unlink()
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", "attacker-key-different-from-production-32+")
    attacker_chain = HashChain(tmp_path)
    attacker_chain.append("e1", "a", {"v": 999})  # forged

    # Restore the legitimate key — verification must now reject.
    monkeypatch.setenv(
        "NOMOS_HASHCHAIN_HMAC_KEY",
        "TEST-ONLY-HMAC-key-do-not-use-in-production-32bytes+++",
    )
    result = verify_chain(tmp_path)
    assert result.valid is False, "rewrite with attacker key must fail verify_chain"
    assert any("HMAC mismatch" in e for e in result.errors)
