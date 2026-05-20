"""M5 (0.3.0) — audit B-F04/F08/F11 regression tests.

Filling the test gaps the QA audit identified after 0.2.0:

- F04: STH signed with key A must NOT verify with key B
- F08: STH on an empty tree (tree_size == 0) is well-defined
- F11: HMAC chain written with key A must NOT verify with key B
       (key-rotation positive + negative scenario)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nomos.core.events import EventType
from nomos.core.hash_chain import HashChain, verify_chain
from nomos.core.merkle import (
    compute_tree_root,
    signed_tree_head,
    verify_signed_tree_head,
)


_KEY_A_HMAC = "a" * 64  # 64 bytes hex-ish — used as raw bytes for HMAC
_KEY_B_HMAC = "b" * 64
_KEY_A_SIGN = "aa" * 32  # 32-byte Ed25519 seed in hex
_KEY_B_SIGN = "bb" * 32


@pytest.fixture
def reset_key_caches():
    """Reset the lru_cache on _signing_key_for so each test sees a
    fresh key for its monkeypatched env."""
    from nomos.core.hash_chain import _hmac_key_for, _signing_key_for

    _hmac_key_for.cache_clear()
    _signing_key_for.cache_clear()
    yield
    _hmac_key_for.cache_clear()
    _signing_key_for.cache_clear()


def _seed_chain(audit_dir: Path, n: int = 3) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    chain = HashChain(storage_dir=audit_dir)
    for i in range(n):
        chain.append(
            event_type=EventType.AGENT_CREATED.value,
            agent_id="x",
            data={"i": i},
        )


# -----------------------------------------------------------------------
# F08 — STH on an empty tree is well-defined.
# -----------------------------------------------------------------------


def test_empty_tree_compute_root_returns_size_zero(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "empty" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    tree_size, root = compute_tree_root(audit_dir)
    assert tree_size == 0
    # Root for empty tree is the sentinel SHA-256("") per RFC 6962.
    import hashlib

    assert root == hashlib.sha256(b"").digest()


def test_empty_tree_sth_signs_and_verifies(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    """STH endpoint on a freshly-hired agent (no chain entries yet) must
    produce a verifiable signature over tree_size == 0. Previously
    untested — audit B-F08."""
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "empty" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    sth = signed_tree_head(audit_dir, origin="nomos-audit/sth")
    assert sth["tree_size"] == 0
    assert len(sth["root_hash"]) == 64
    assert len(sth["signature"]) == 128
    assert verify_signed_tree_head(sth) is True


# -----------------------------------------------------------------------
# F04 — STH signed with key A must NOT verify with key B.
# -----------------------------------------------------------------------


def test_sth_signed_with_one_key_does_not_verify_with_another(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "agent" / "audit"
    _seed_chain(audit_dir, n=3)
    sth = signed_tree_head(audit_dir, origin="nomos-audit/sth")
    assert verify_signed_tree_head(sth) is True, "STH must verify with the signing key"

    # Rotate the env to a different Ed25519 seed; reset the lru_cache so
    # _signing_key picks up the new env.
    from nomos.core.hash_chain import _signing_key_for

    _signing_key_for.cache_clear()
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_B_SIGN)
    assert verify_signed_tree_head(sth) is False, (
        "STH must NOT verify with a different Ed25519 key — non-repudiation contract."
    )


# -----------------------------------------------------------------------
# F11 — Key-rotation scenario: chain written under key A, verified
# under key B, must report HMAC mismatch.
# -----------------------------------------------------------------------


def test_chain_written_under_key_a_does_not_verify_under_key_b(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "rot" / "audit"
    _seed_chain(audit_dir, n=3)
    res_a = verify_chain(audit_dir)
    assert res_a.valid, f"chain under key A must verify: {res_a.errors}"

    # Rotate HMAC AND signing keys. Reset caches so the new env is read.
    from nomos.core.hash_chain import _hmac_key_for, _signing_key_for

    _hmac_key_for.cache_clear()
    _signing_key_for.cache_clear()
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_B_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_B_SIGN)

    res_b = verify_chain(audit_dir)
    assert not res_b.valid, "chain written under key A MUST NOT verify under key B"
    # Both HMAC and Ed25519 errors should surface for each of the 3 entries.
    assert any("HMAC mismatch" in e for e in res_b.errors), res_b.errors
    assert any("Ed25519 signature mismatch" in e for e in res_b.errors), res_b.errors


# -----------------------------------------------------------------------
# Stripping the env mid-flight is fail-closed (regression for L038).
# -----------------------------------------------------------------------


def test_verify_chain_fails_closed_when_keys_missing(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "f" / "audit"
    _seed_chain(audit_dir, n=2)

    # Strip BOTH keys after writing — verify_chain must raise fail-closed.
    from nomos.core.hash_chain import (
        AuditSignatureKeyMissing,
        HashChainKeyMissing,
        _hmac_key_for,
        _signing_key_for,
    )

    _hmac_key_for.cache_clear()
    _signing_key_for.cache_clear()
    monkeypatch.delenv("NOMOS_HASHCHAIN_HMAC_KEY", raising=False)
    monkeypatch.delenv("NOMOS_AUDIT_SIGNING_KEY", raising=False)

    with pytest.raises((HashChainKeyMissing, AuditSignatureKeyMissing)):
        verify_chain(audit_dir)


# -----------------------------------------------------------------------
# Defensive: stripping ONLY the signing key still fails-closed.
# -----------------------------------------------------------------------


def test_verify_chain_fails_closed_when_only_signing_key_missing(tmp_path: Path, monkeypatch, reset_key_caches) -> None:
    monkeypatch.setenv("NOMOS_HASHCHAIN_HMAC_KEY", _KEY_A_HMAC)
    monkeypatch.setenv("NOMOS_AUDIT_SIGNING_KEY", _KEY_A_SIGN)
    audit_dir = tmp_path / "f2" / "audit"
    _seed_chain(audit_dir, n=2)

    from nomos.core.hash_chain import (
        AuditSignatureKeyMissing,
        _signing_key_for,
    )

    _signing_key_for.cache_clear()
    monkeypatch.delenv("NOMOS_AUDIT_SIGNING_KEY", raising=False)
    # Force env to empty so _signing_key sees it as missing.
    os.environ["NOMOS_AUDIT_SIGNING_KEY"] = ""

    with pytest.raises(AuditSignatureKeyMissing):
        verify_chain(audit_dir)
