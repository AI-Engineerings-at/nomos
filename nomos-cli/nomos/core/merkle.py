"""RFC 6962 Merkle tree over the audit hash-chain entries.

Phase-B1: an embedded transparency-log layer in addition to the linear
hash chain. Each chain entry's content hash becomes a leaf in a Merkle
tree; the signed root (STH) lets a third party prove that any specific
entry is included in a chain head WITHOUT requiring the full chain.

Compatibility:
* Leaf hashing: ``SHA-256(0x00 || leaf_data)`` (RFC 6962 Section 2.1).
* Internal hashing: ``SHA-256(0x01 || left || right)``.
* Inclusion-proof algorithm: RFC 6962 Section 2.1.1.
* Signed Tree Head (STH) shape: ``{origin, tree_size, root_hash,
  timestamp, signature}`` — close to Sigstore/Rekor checkpoint notes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .hash_chain import (
    CHAIN_FILENAME,
    _compute_signature,
    _verify_signature,
)

# RFC 6962 domain-separation bytes.
_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def _hash_leaf(data: bytes) -> bytes:
    return hashlib.sha256(_LEAF_PREFIX + data).digest()


def _hash_node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(_NODE_PREFIX + left + right).digest()


def _largest_power_of_two_less_than(n: int) -> int:
    """k = largest power of 2 < n (n >= 2)."""
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def _mth_range(leaves: list[bytes], start: int, end: int) -> bytes:
    """RFC 6962 Merkle Tree Hash over leaves[start:end].

    Uses (start, end) indices instead of `leaves[start:end]` slicing so
    each call is O(1) memory; total tree build is O(n) compute + O(log n)
    stack depth. Audit A-#12 flagged the previous slice-based variant as
    an O(n log n) memory amplification under user-supplied tree size.
    """
    n = end - start
    if n == 0:
        return hashlib.sha256(b"").digest()
    if n == 1:
        return leaves[start]
    k = _largest_power_of_two_less_than(n)
    return _hash_node(
        _mth_range(leaves, start, start + k),
        _mth_range(leaves, start + k, end),
    )


def _mth(leaves: list[bytes]) -> bytes:
    """RFC 6962 Merkle Tree Hash (top-level entry).

    Empty tree returns SHA-256("") sentinel per RFC; callers branch on
    `tree_size == 0` before signing it as a real STH root.
    """
    return _mth_range(leaves, 0, len(leaves))


def _path_range(m: int, leaves: list[bytes], start: int, end: int) -> list[bytes]:
    """RFC 6962 inclusion-proof path for leaf index m within leaves[start:end].

    Index-based to match `_mth_range`'s O(log n) memory profile.
    """
    n = end - start
    if n == 1:
        return []
    k = _largest_power_of_two_less_than(n)
    if m < k:
        return _path_range(m, leaves, start, start + k) + [_mth_range(leaves, start + k, end)]
    return _path_range(m - k, leaves, start + k, end) + [_mth_range(leaves, start, start + k)]


def _path(m: int, leaves: list[bytes]) -> list[bytes]:
    """RFC 6962 inclusion-proof path (top-level entry)."""
    return _path_range(m, leaves, 0, len(leaves))


def _read_leaf_hashes(storage_dir: Path) -> list[bytes]:
    """Read the chain.jsonl and return the per-entry leaf hashes.

    The leaf data is the canonical SHA-256 entry hash already stored
    in each chain line (`hash` field). We hash THAT again with the
    RFC 6962 leaf prefix so the Merkle tree's leaf domain is distinct
    from raw entry hashes.
    """
    chain_file = storage_dir / CHAIN_FILENAME
    if not chain_file.exists():
        return []
    leaves: list[bytes] = []
    for line in chain_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        entry_hash_hex = obj.get("hash")
        if not entry_hash_hex:
            continue
        leaves.append(_hash_leaf(entry_hash_hex.encode("utf-8")))
    return leaves


def compute_tree_root(storage_dir: Path) -> tuple[int, bytes]:
    """Return ``(tree_size, merkle_root_bytes)`` for an agent's chain.

    Tree size of 0 yields the canonical empty-tree hash; callers
    typically branch on tree_size == 0.
    """
    leaves = _read_leaf_hashes(storage_dir)
    return len(leaves), _mth(leaves)


def signed_tree_head(storage_dir: Path, origin: str) -> dict:
    """Produce a Sigstore-Rekor-style signed checkpoint note.

    The signature is computed over the canonical body
    ``f"{origin}\\n{tree_size}\\n{root_hash_hex}\\n{timestamp}"`` using
    the same Ed25519 key that signs chain entries. A verifier with only
    the public key + this body can confirm the STH.
    """
    tree_size, root = compute_tree_root(storage_dir)
    root_hex = root.hex()
    ts = datetime.now(timezone.utc).isoformat()
    body = f"{origin}\n{tree_size}\n{root_hex}\n{ts}"
    body_hash_hex = hashlib.sha256(body.encode("utf-8")).hexdigest()
    sig = _compute_signature(body_hash_hex)
    return {
        "origin": origin,
        "tree_size": tree_size,
        "root_hash": root_hex,
        "timestamp": ts,
        "signature": sig,
    }


def verify_signed_tree_head(sth: dict) -> bool:
    """Verify a previously-produced STH against the current Ed25519 key."""
    try:
        origin = str(sth["origin"])
        tree_size = int(sth["tree_size"])
        root_hex = str(sth["root_hash"])
        ts = str(sth["timestamp"])
        sig = str(sth["signature"])
    except (KeyError, TypeError, ValueError):
        return False
    body = f"{origin}\n{tree_size}\n{root_hex}\n{ts}"
    body_hash_hex = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return _verify_signature(body_hash_hex, sig)


def inclusion_proof(storage_dir: Path, leaf_index: int) -> dict:
    """Return an RFC 6962 inclusion proof for the ``leaf_index``-th leaf.

    Response shape::

        {
            "leaf_index": int,
            "tree_size": int,
            "root_hash": hex,
            "audit_path": [hex, ...],
        }

    A verifier reconstructs the root from the leaf + the audit path
    and compares to ``root_hash``.
    """
    leaves = _read_leaf_hashes(storage_dir)
    n = len(leaves)
    if leaf_index < 0 or leaf_index >= n:
        raise IndexError(f"leaf_index {leaf_index} out of range [0,{n})")
    path = _path(leaf_index, leaves)
    return {
        "leaf_index": leaf_index,
        "tree_size": n,
        "root_hash": _mth(leaves).hex(),
        "audit_path": [h.hex() for h in path],
    }


def verify_inclusion_proof(
    leaf_data: bytes,
    leaf_index: int,
    tree_size: int,
    audit_path_hex: list[str],
    root_hash_hex: str,
) -> bool:
    """Recompute the root from leaf + audit path and compare. RFC 6962
    Section 2.1.1.

    ``leaf_data`` is the same input that was hashed into the leaf
    (i.e. the chain entry's content-hash hex bytes for our usage).

    Audit B-F05 / L039: malformed inputs (non-hex sibling, non-hex root)
    return ``False`` instead of raising — the function is part of the
    regulator-facing verifier API and MUST never crash the caller on
    corrupt-by-design input.
    """
    if leaf_index < 0 or leaf_index >= tree_size:
        return False
    if not isinstance(audit_path_hex, list):
        return False
    try:
        node = _hash_leaf(leaf_data)
        fn = leaf_index
        sn = tree_size - 1
        for sibling_hex in audit_path_hex:
            sibling = bytes.fromhex(sibling_hex)
            if fn % 2 == 1 or fn == sn:
                node = _hash_node(sibling, node)
                while fn % 2 == 0 and sn > 0:
                    fn >>= 1
                    sn >>= 1
            else:
                node = _hash_node(node, sibling)
            fn >>= 1
            sn >>= 1
        return node.hex() == root_hash_hex
    except (ValueError, TypeError):
        # bytes.fromhex on non-hex / non-string input.
        return False
