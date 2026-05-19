"""NomOS Hash Chain — tamper-evident audit trail.

Each entry contains a SHA-256 hash computed over (sequence + timestamp +
event_type + agent_id + data + previous_hash). Changing any entry
invalidates all subsequent hashes, making tampering detectable.

Storage: JSONL file (one JSON object per line), human-readable,
exportable for regulators.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


CHAIN_FILENAME = "chain.jsonl"
GENESIS_HASH = "0" * 64

# M3: HMAC anchoring. The plain SHA-256 chain is fully recomputable, so a
# consistent rewrite of the JSONL file passes verify_chain. An HMAC over each
# entry's content hash, keyed by a secret the attacker does not have, makes
# any tampering detectable even on a writable volume.
#
# The key is env-injectable via NOMOS_HASHCHAIN_HMAC_KEY (inject from Vault in
# production). There is NO fallback: a missing key fails closed. Tests inject
# the key via conftest. Length must be >= 32 bytes (HMAC-SHA256 best practice).
_HMAC_ENV_VAR = "NOMOS_HASHCHAIN_HMAC_KEY"
_HMAC_MIN_KEY_BYTES = 32


class HashChainKeyMissing(RuntimeError):
    """Raised when NOMOS_HASHCHAIN_HMAC_KEY is unset or too short.

    Fail-closed: under no circumstances should the hash-chain operate with a
    weak/missing key. A weak key reduces HMAC anchoring to security theater.
    """


def _hmac_key() -> bytes:
    """Resolve the HMAC key. Fail-closed on missing/short key."""
    raw = os.environ.get(_HMAC_ENV_VAR, "")
    if not raw or len(raw.encode("utf-8")) < _HMAC_MIN_KEY_BYTES:
        raise HashChainKeyMissing(
            f"{_HMAC_ENV_VAR} must be set and >= {_HMAC_MIN_KEY_BYTES} bytes "
            "(inject from Vault in production; configure in tests/conftest)."
        )
    return raw.encode("utf-8")


def _compute_hmac(content_hash: str) -> str:
    """Compute the HMAC-SHA256 anchor over an entry's content hash."""
    return hmac.new(_hmac_key(), content_hash.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class HashChainEntry:
    """A single entry in the audit hash chain."""

    sequence: int
    timestamp: str
    event_type: str
    agent_id: str
    data: dict
    previous_hash: str
    hash: str = field(init=False)
    hmac: str = field(init=False)

    def __post_init__(self) -> None:
        canonical = json.dumps(
            {
                "sequence": self.sequence,
                "timestamp": self.timestamp,
                "event_type": self.event_type,
                "agent_id": self.agent_id,
                "data": self.data,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        object.__setattr__(self, "hash", computed)
        object.__setattr__(self, "hmac", _compute_hmac(computed))

    def to_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "hmac": self.hmac,
        }


@dataclass
class VerifyResult:
    """Result of chain verification."""

    valid: bool
    entries_checked: int
    errors: list[str] = field(default_factory=list)


class HashChain:
    """Append-only hash chain backed by a JSONL file."""

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._storage_dir / CHAIN_FILENAME
        self._entries: list[HashChainEntry] = []
        self._load()

    def _load(self) -> None:
        if not self._file.exists():
            return
        for i, line in enumerate(self._file.read_text(encoding="utf-8").strip().split("\n")):
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Corrupt hash chain at line {i}: {exc}") from exc
            entry = HashChainEntry(
                sequence=raw["sequence"],
                timestamp=raw["timestamp"],
                event_type=raw["event_type"],
                agent_id=raw["agent_id"],
                data=raw["data"],
                previous_hash=raw["previous_hash"],
            )
            self._entries.append(entry)

    @property
    def entries(self) -> list[HashChainEntry]:
        """Public read-only access to chain entries."""
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def append(
        self,
        event_type: str,
        agent_id: str,
        data: dict,
    ) -> HashChainEntry:
        previous_hash = self._entries[-1].hash if self._entries else GENESIS_HASH
        entry = HashChainEntry(
            sequence=len(self._entries),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            agent_id=agent_id,
            data=data,
            previous_hash=previous_hash,
        )
        self._entries.append(entry)
        with self._file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
        return entry


def verify_chain(storage_dir: Path) -> VerifyResult:
    """Verify the integrity of a hash chain.

    Recomputes every hash from scratch and checks that:
    1. Each entry's hash matches its content.
    2. Each entry's previous_hash matches the prior entry's hash.
    3. The first entry's previous_hash is the genesis hash.
    4. (M3) When an entry carries an ``hmac`` field, the HMAC is recomputed
       with the configured key and must match. Tampering without the key is
       therefore detectable even if the SHA-256 chain is consistently
       rewritten. Legacy entries written before HMAC anchoring (no ``hmac``
       field) are still accepted on the SHA-256 chain alone for backward
       compatibility.
    """
    chain_file = storage_dir / CHAIN_FILENAME
    if not chain_file.exists():
        return VerifyResult(valid=True, entries_checked=0)

    lines = chain_file.read_text(encoding="utf-8").strip().split("\n")
    lines = [ln for ln in lines if ln]
    if not lines:
        return VerifyResult(valid=True, entries_checked=0)

    errors: list[str] = []
    previous_hash = GENESIS_HASH

    for i, line in enumerate(lines):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"Entry {i}: corrupt JSON — cannot parse line")
            break

        stored_hash = raw.get("hash", "")

        recomputed = HashChainEntry(
            sequence=raw["sequence"],
            timestamp=raw["timestamp"],
            event_type=raw["event_type"],
            agent_id=raw["agent_id"],
            data=raw["data"],
            previous_hash=raw["previous_hash"],
        )

        if recomputed.hash != stored_hash:
            errors.append(
                f"Entry {i}: hash mismatch (stored={stored_hash[:16]}..., computed={recomputed.hash[:16]}...)"
            )

        # M3+H4 (post-judgment-day): HMAC anchoring is MANDATORY for every
        # entry. A missing `hmac` field would let an attacker drop the field
        # to bypass integrity — that legacy escape hatch is closed. Recompute
        # over the *stored* hash so a forged hash with a stale HMAC is caught.
        stored_hmac = raw.get("hmac")
        if stored_hmac is None:
            errors.append(f"Entry {i}: missing HMAC field — integrity not anchored")
        else:
            expected_hmac = _compute_hmac(stored_hash)
            if not hmac.compare_digest(expected_hmac, str(stored_hmac)):
                errors.append(
                    f"Entry {i}: HMAC mismatch — entry tampered or wrong key (stored={str(stored_hmac)[:16]}...)"
                )

        if raw["previous_hash"] != previous_hash:
            errors.append(
                f"Entry {i}: chain broken (expected previous={previous_hash[:16]}..., "
                f"got={raw['previous_hash'][:16]}...)"
            )

        # Use recomputed hash as baseline — not the potentially tampered stored hash
        previous_hash = recomputed.hash

    return VerifyResult(
        valid=len(errors) == 0,
        entries_checked=len(lines),
        errors=errors,
    )
