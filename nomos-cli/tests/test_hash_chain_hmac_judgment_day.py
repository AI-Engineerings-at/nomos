"""Regression tests for the post-judgment-day hash-chain hardening.

C1: _hmac_key() fails closed when NOMOS_HASHCHAIN_HMAC_KEY is missing/short.
H4: verify_chain rejects entries that have NO `hmac` field (legacy bypass closed).
Phase-A1: Ed25519 signature per entry — mandatory, missing signature is
          rejected, forged signature with attacker key is rejected, fail-
          closed when NOMOS_AUDIT_SIGNING_KEY is missing or malformed.
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


# ---------------------------------------------------------------------------
# Phase-A1: Ed25519 per-entry signature regression tests.
# ---------------------------------------------------------------------------


def test_signing_key_fails_closed_without_env(monkeypatch) -> None:
    from nomos.core.hash_chain import AuditSignatureKeyMissing, _signing_key

    monkeypatch.delenv("NOMOS_AUDIT_SIGNING_KEY", raising=False)
    with pytest.raises(AuditSignatureKeyMissing):
        _signing_key()


def test_signing_key_fails_closed_with_wrong_length(monkeypatch) -> None:
    from nomos.core.hash_chain import AuditSignatureKeyMissing, _signing_key

    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", "abcdef")  # too short
    with pytest.raises(AuditSignatureKeyMissing):
        _signing_key()


def test_signing_key_fails_closed_with_non_hex(monkeypatch) -> None:
    from nomos.core.hash_chain import AuditSignatureKeyMissing, _signing_key

    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", "G" * 64)  # 64 chars but not hex
    with pytest.raises(AuditSignatureKeyMissing):
        _signing_key()


def test_entry_has_signature_and_verifies(tmp_path: Path) -> None:
    chain = HashChain(storage_dir=tmp_path)
    entry = chain.append(event_type="agent.created", agent_id="a", data={"x": 1})
    assert entry.signature, "every entry must carry an Ed25519 signature"
    assert len(entry.signature) == 128, "Ed25519 signature is 64 bytes = 128 hex chars"
    result = verify_chain(tmp_path)
    assert result.valid is True, f"freshly written chain must verify, errors: {result.errors}"


def test_verify_chain_rejects_entries_without_signature_field(tmp_path: Path) -> None:
    """Drop-the-signature-field attack must NOT verify (analogue of the
    drop-hmac-field attack closed in H4)."""
    chain = HashChain(storage_dir=tmp_path)
    chain.append(event_type="agent.created", agent_id="a", data={"x": 1})
    p = tmp_path / CHAIN_FILENAME
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    stripped = []
    for ln in lines:
        obj = json.loads(ln)
        obj.pop("signature", None)
        stripped.append(json.dumps(obj, sort_keys=True, separators=(",", ":")))
    p.write_text("\n".join(stripped) + "\n", encoding="utf-8")
    result = verify_chain(tmp_path)
    assert result.valid is False, "missing-signature attack must fail verify_chain"
    assert any("missing Ed25519 signature" in e for e in result.errors)


def test_verify_chain_rejects_signature_from_attacker_key(tmp_path: Path, monkeypatch) -> None:
    """An attacker who can write the file but only has THEIR OWN Ed25519
    key cannot produce a valid signature against the legitimate verify
    key — verify_chain must reject."""
    # Step 1: legitimate entries written with the real test key.
    chain = HashChain(storage_dir=tmp_path)
    chain.append(event_type="agent.created", agent_id="a", data={"v": 1})

    # Step 2: attacker rewrites with a DIFFERENT signing key. SHA-256 + HMAC
    # would all recompute consistent; only the Ed25519 signature differs.
    p = tmp_path / CHAIN_FILENAME
    p.unlink()
    monkeypatch.setenv(
        "NOMOS_AUDIT_SIGNING_KEY",
        "f00dface" + "0" * 56,  # 64 hex chars, different from the test default
    )
    attacker = HashChain(storage_dir=tmp_path)
    attacker.append(event_type="agent.created", agent_id="a", data={"v": 999})

    # Step 3: restore the legitimate key — verify must reject the forged
    # signature.
    monkeypatch.setenv(
        "NOMOS_AUDIT_SIGNING_KEY",
        "deadbeefcafebabe0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    result = verify_chain(tmp_path)
    assert result.valid is False, "forged signature with attacker key must fail"
    assert any("Ed25519 signature mismatch" in e for e in result.errors)
