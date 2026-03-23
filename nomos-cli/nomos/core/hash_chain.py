"""NomOS Hash Chain — tamper-evident audit trail.

Each entry contains a SHA-256 hash computed over (sequence + timestamp +
event_type + agent_id + data + previous_hash). Changing any entry
invalidates all subsequent hashes, making tampering detectable.

Storage: JSONL file (one JSON object per line), human-readable,
exportable for regulators.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


CHAIN_FILENAME = "chain.jsonl"
GENESIS_HASH = "0" * 64


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

    def to_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
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
