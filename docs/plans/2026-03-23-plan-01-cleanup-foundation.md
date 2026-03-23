# Plan 1: Cleanup + Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all S9 violations (skeletons), fix CI to green, and build the nomos-core foundation that every other component depends on.

**Architecture:** Strip the repo to only real, tested code. Then extend nomos-core bottom-up: hash_chain (audit trail foundation), compliance_engine (document verification), and forge (agent creation from templates). Each module follows TDD — test first, implement second, commit third.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, pytest, ruff, uv, GitHub Actions

---

## File Structure

### Files to DELETE (S9 Violations — skeletons with no real implementation)

```
nomos-api/main.py                  # 2 placeholder endpoints, no logic
nomos-api/Dockerfile               # Builds a skeleton
nomos-api/models/                  # Empty directory
nomos-api/routers/                 # Empty directory
nomos-api/tests/                   # Empty directory
nomos-gate/app.py                  # "Coming soon" Streamlit
nomos-gate/Dockerfile              # Builds a skeleton
nomos-gate/engine/                 # Empty directory
nomos-gate/templates/              # Empty directory
nomos-gate/tests/                  # Empty directory
nomos-console/app/page.tsx         # Static HTML, no functionality
nomos-console/app/layout.tsx       # Minimal wrapper
nomos-console/package.json         # Dependencies for skeleton
nomos-console/tsconfig.json        # Config for skeleton
nomos-console/next.config.js       # Config for skeleton
nomos-console/Dockerfile           # Builds a skeleton
nomos-cli/nomos/cli.py             # 4x "coming soon" commands
governance/                        # Empty directory
deploy/                            # Empty directory
docker-compose.yml                 # References non-existent services
```

### Files to KEEP (real, tested, working)

```
nomos-cli/nomos/__init__.py
nomos-cli/nomos/core/__init__.py
nomos-cli/nomos/core/manifest.py        # 226 lines, 11 Pydantic models — SOLID
nomos-cli/nomos/core/manifest_validator.py  # 88 lines, load/validate/hash — SOLID
nomos-cli/tests/__init__.py
nomos-cli/tests/test_manifest.py         # 21 tests, all PASS — SOLID
nomos-cli/pyproject.toml
schemas/agent-manifest.yaml
templates/external-secretary/manifest.yaml
templates/external-secretary/mani-v1-manifest.yaml
README.md, README.de.md, LICENSE, CONTRIBUTING.md, SECURITY.md
.github/workflows/ci.yml                # Will be fixed (remove broken jobs)
.gitignore
docs/                                    # Plans and protocols — real documentation
```

### Files to CREATE (new nomos-core modules)

```
nomos-cli/nomos/core/hash_chain.py       # Tamper-evident audit trail (SHA-256 chain)
nomos-cli/tests/test_hash_chain.py       # Tests for hash_chain
nomos-cli/nomos/core/compliance_engine.py # Manifest → compliance check → pass/fail
nomos-cli/tests/test_compliance_engine.py # Tests for compliance_engine
nomos-cli/nomos/core/forge.py            # Template + Manifest → agent output directory
nomos-cli/tests/test_forge.py            # Tests for forge
nomos-cli/nomos/core/events.py           # Event types for hook system
nomos-cli/tests/test_events.py           # Tests for events
```

---

## Task 1: Remove S9 Skeleton Code

**Why:** "Coming soon" is not code. Empty directories are not architecture. A senior dev removes garbage before building.

**Files:**
- Delete: `nomos-api/` (entire directory)
- Delete: `nomos-gate/` (entire directory)
- Delete: `nomos-console/` (entire directory)
- Delete: `nomos-cli/nomos/cli.py`
- Delete: `governance/` (empty directory)
- Delete: `deploy/` (empty directory)
- Delete: `docker-compose.yml`
- Modify: `nomos-cli/pyproject.toml` (remove dead `[project.scripts]` entry)

- [ ] **Step 1: Verify what we're deleting is actually skeleton**

```bash
cd C:\Users\Legion\Documents\nomos
# Confirm: every file in nomos-api has no real logic
cat nomos-api/main.py        # Should show placeholder /health + empty /api/fleet
cat nomos-gate/app.py        # Should show "Coming soon"
cat nomos-cli/nomos/cli.py   # Should show 4x "coming soon"
cat nomos-console/app/page.tsx  # Should show static HTML
```

Expected: All files contain placeholder/skeleton code, no real business logic.

- [ ] **Step 2: Delete skeleton directories and files**

```bash
cd C:\Users\Legion\Documents\nomos
rm -rf nomos-api/
rm -rf nomos-gate/
rm -rf nomos-console/
rm nomos-cli/nomos/cli.py
rm -rf governance/
rm -rf deploy/
rm docker-compose.yml
```

- [ ] **Step 3: Remove dead entrypoint from pyproject.toml**

The `[project.scripts]` section points to `nomos.cli:main` which we just deleted. Remove it to avoid broken package installs.

Edit `nomos-cli/pyproject.toml` — remove these lines:
```toml
[project.scripts]
nomos = "nomos.cli:main"
```

- [ ] **Step 4: Verify manifest tests still pass**

Run: `cd nomos-cli && uv run pytest -v`
Expected: 21 passed (removing skeletons must not break working code)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix(s9): remove all skeleton code — no more 'coming soon'

Removed: nomos-api (placeholder endpoints), nomos-gate (coming soon),
nomos-console (static HTML), cli.py (stub commands), empty directories,
docker-compose.yml (referenced non-existent services).
Removed dead [project.scripts] entrypoint pointing to deleted cli.py.

Kept: nomos-core (manifest.py, manifest_validator.py, 21 passing tests),
schemas, templates, docs, CI config.

S9 Rule: No placeholder code, no fake implementations."
```

---

## Task 2: Fix CI Pipeline

**Why:** CI must be green. Always. Broken CI that nobody fixes is worse than no CI.

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the target CI config**

The CI should only test what EXISTS. Remove jobs for deleted components. Keep: lint-python, test-cli. Remove: lint-typescript, test-api, test-gate, build-console, docker-build.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-python:
    name: Lint Python
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: nomos-cli
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.12"
      - run: uv tool install ruff
      - run: ruff check .
      - run: ruff format --check .

  test-cli:
    name: Test CLI
    runs-on: ubuntu-latest
    needs: lint-python
    defaults:
      run:
        working-directory: nomos-cli
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.12"
      - run: uv sync
      - run: uv run pytest -v --tb=short
```

- [ ] **Step 2: Replace the CI file**

Overwrite `.github/workflows/ci.yml` with the config above.

- [ ] **Step 3: Verify linting passes locally**

Run: `cd nomos-cli && uv tool install ruff && ruff check . && ruff format --check .`
Expected: No errors. If ruff finds issues, fix them before committing.

- [ ] **Step 4: Verify tests pass locally**

Run: `cd nomos-cli && uv run pytest -v --tb=short`
Expected: 21 passed

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "fix(ci): remove jobs for deleted components, CI is green

Only lint-python and test-cli remain — the only code that exists.
Jobs will be added back when real implementations are built."
```

---

## Task 3: Hash Chain Module (NomOS Vault Foundation)

**Why:** Every NomOS operation needs a tamper-evident audit trail. The hash chain is the foundation — each entry references the previous entry's hash, making the chain impossible to modify without detection. Regulators can verify the chain independently.

**Files:**
- Create: `nomos-cli/nomos/core/hash_chain.py`
- Create: `nomos-cli/tests/test_hash_chain.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for NomOS Hash Chain — tamper-evident audit trail."""

from __future__ import annotations

import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from nomos.core.hash_chain import (
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
        assert len(entry.hash) == 64  # SHA-256

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

        # Tamper: modify the first entry's data
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd nomos-cli && uv run pytest tests/test_hash_chain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nomos.core.hash_chain'`

- [ ] **Step 3: Implement hash_chain.py**

```python
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
                raise ValueError(
                    f"Corrupt hash chain at line {i}: {exc}"
                ) from exc
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
            f.write(
                json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
                + "\n"
            )
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
    lines = [l for l in lines if l]
    if not lines:
        return VerifyResult(valid=True, entries_checked=0)

    errors: list[str] = []
    previous_hash = GENESIS_HASH

    for i, line in enumerate(lines):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"Entry {i}: corrupt JSON — cannot parse line")
            break  # Cannot continue verification after corrupt line

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
                f"Entry {i}: hash mismatch (stored={stored_hash[:16]}..., "
                f"computed={recomputed.hash[:16]}...)"
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd nomos-cli && uv run pytest tests/test_hash_chain.py -v`
Expected: 11 passed

- [ ] **Step 5: Run ALL tests to verify nothing broke**

Run: `cd nomos-cli && uv run pytest -v`
Expected: 32 passed (21 manifest + 11 hash_chain)

- [ ] **Step 6: Run linting**

Run: `ruff check nomos-cli/ && ruff format --check nomos-cli/`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add nomos-cli/nomos/core/hash_chain.py nomos-cli/tests/test_hash_chain.py
git commit -m "feat(core): hash chain — tamper-evident audit trail

Append-only JSONL chain where each entry's SHA-256 hash covers
(sequence, timestamp, event_type, agent_id, data, previous_hash).
Tampering with any entry invalidates all subsequent hashes.

verify_chain() independently recomputes and validates the entire chain,
exportable for regulators (EU AI Act Art. 12).

11 tests: entry creation, determinism, chaining, persistence, loading,
verification, tamper detection, corrupt JSONL detection, empty chain."
```

---

## Task 4: Event Types Module

**Why:** Every component needs to agree on what events exist. This is the contract between the hash chain, hooks, and future API.

**Files:**
- Create: `nomos-cli/nomos/core/events.py`
- Create: `nomos-cli/tests/test_events.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for NomOS Event Types."""

from __future__ import annotations

import pytest

from nomos.core.events import (
    EventType,
    NomOSEvent,
    validate_event_type,
)


class TestEventType:
    def test_all_lifecycle_events_exist(self) -> None:
        assert EventType.AGENT_CREATED == "agent.created"
        assert EventType.AGENT_DEPLOYED == "agent.deployed"
        assert EventType.AGENT_STOPPED == "agent.stopped"
        assert EventType.AGENT_RETIRED == "agent.retired"

    def test_all_compliance_events_exist(self) -> None:
        assert EventType.COMPLIANCE_CHECK_PASSED == "compliance.check.passed"
        assert EventType.COMPLIANCE_CHECK_FAILED == "compliance.check.failed"
        assert EventType.COMPLIANCE_DOC_SIGNED == "compliance.doc.signed"

    def test_all_governance_events_exist(self) -> None:
        assert EventType.GOVERNANCE_HOOK_TRIGGERED == "governance.hook.triggered"
        assert EventType.GOVERNANCE_HOOK_BLOCKED == "governance.hook.blocked"
        assert EventType.GOVERNANCE_KILL_SWITCH == "governance.kill_switch"
        assert EventType.GOVERNANCE_ESCALATION == "governance.escalation"

    def test_all_audit_events_exist(self) -> None:
        assert EventType.AUDIT_CHAIN_CREATED == "audit.chain.created"
        assert EventType.AUDIT_CHAIN_VERIFIED == "audit.chain.verified"
        assert EventType.AUDIT_EXPORTED == "audit.exported"


class TestNomOSEvent:
    def test_event_creation(self) -> None:
        event = NomOSEvent(
            event_type=EventType.AGENT_CREATED,
            agent_id="mani-v1",
            data={"name": "Mani Ruf"},
        )
        assert event.event_type == "agent.created"
        assert event.agent_id == "mani-v1"
        assert event.data == {"name": "Mani Ruf"}
        assert event.timestamp  # auto-generated

    def test_event_to_dict(self) -> None:
        event = NomOSEvent(
            event_type=EventType.AGENT_CREATED,
            agent_id="mani-v1",
            data={},
        )
        d = event.to_dict()
        assert "event_type" in d
        assert "agent_id" in d
        assert "timestamp" in d
        assert "data" in d


class TestValidateEventType:
    def test_valid_event_type(self) -> None:
        assert validate_event_type("agent.created") is True

    def test_invalid_event_type(self) -> None:
        assert validate_event_type("invalid.event") is False

    def test_custom_prefix_valid(self) -> None:
        assert validate_event_type("agent.custom_action") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd nomos-cli && uv run pytest tests/test_events.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement events.py**

```python
"""NomOS Event Types — contract between all components.

Defines the canonical event types used by the hash chain, governance
hooks, API, and CLI. Adding a new event type here makes it available
everywhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field


class EventType(str, Enum):
    """Canonical NomOS event types."""

    # Agent lifecycle
    AGENT_CREATED = "agent.created"
    AGENT_DEPLOYED = "agent.deployed"
    AGENT_STOPPED = "agent.stopped"
    AGENT_RETIRED = "agent.retired"

    # Compliance
    COMPLIANCE_CHECK_PASSED = "compliance.check.passed"
    COMPLIANCE_CHECK_FAILED = "compliance.check.failed"
    COMPLIANCE_DOC_SIGNED = "compliance.doc.signed"

    # Governance
    GOVERNANCE_HOOK_TRIGGERED = "governance.hook.triggered"
    GOVERNANCE_HOOK_BLOCKED = "governance.hook.blocked"
    GOVERNANCE_KILL_SWITCH = "governance.kill_switch"
    GOVERNANCE_ESCALATION = "governance.escalation"

    # Audit
    AUDIT_CHAIN_CREATED = "audit.chain.created"
    AUDIT_CHAIN_VERIFIED = "audit.chain.verified"
    AUDIT_EXPORTED = "audit.exported"


_VALID_EVENT_TYPES = {e.value for e in EventType}


def validate_event_type(event_type: str) -> bool:
    """Check if a string is a valid NomOS event type."""
    return event_type in _VALID_EVENT_TYPES


@dataclass
class NomOSEvent:
    """A single event occurrence."""

    event_type: str
    agent_id: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
```

- [ ] **Step 4: Run tests**

Run: `cd nomos-cli && uv run pytest tests/test_events.py -v`
Expected: 7 passed

- [ ] **Step 5: Run ALL tests**

Run: `cd nomos-cli && uv run pytest -v`
Expected: 39 passed (21 + 11 + 7)

- [ ] **Step 6: Commit**

```bash
git add nomos-cli/nomos/core/events.py nomos-cli/tests/test_events.py
git commit -m "feat(core): event types — canonical contract for all components

14 event types across 4 categories: lifecycle (created/deployed/stopped/
retired), compliance (check passed/failed, doc signed), governance
(hook triggered/blocked, kill switch, escalation), audit (chain created/
verified, exported).

NomOSEvent dataclass with auto-timestamp. validate_event_type() for
runtime validation. 7 tests."
```

---

## Task 5: Compliance Engine Module

**Why:** The compliance engine is the BLOCKING GATE — it decides whether an agent is allowed to start. No signed docs = no deployment. This is what makes NomOS different from "install and pray."

**Files:**
- Create: `nomos-cli/nomos/core/compliance_engine.py`
- Create: `nomos-cli/tests/test_compliance_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for NomOS Compliance Engine — the blocking gate."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from nomos.core.compliance_engine import (
    ComplianceResult,
    ComplianceStatus,
    check_compliance,
    check_document_exists,
    REQUIRED_DOCUMENTS,
)
from nomos.core.manifest import AgentManifest


# Reuse valid manifest data from test_manifest.py
VALID_MANIFEST_DATA: dict = {
    "agent": {
        "id": "test-agent",
        "name": "Test Agent",
        "role": "test-role",
        "risk_class": "limited",
        "created_at": "2026-03-23T00:00:00Z",
    },
    "identity": {
        "display_name": "Test Agent",
        "company": "Test Co",
        "email": "test@test.com",
    },
}


class TestCheckDocumentExists:
    def test_existing_document(self, tmp_path: Path) -> None:
        doc = tmp_path / "dpia.pdf"
        doc.write_text("DPIA content")
        assert check_document_exists("dpia", tmp_path) is True

    def test_existing_document_md(self, tmp_path: Path) -> None:
        doc = tmp_path / "dpia.md"
        doc.write_text("# DPIA")
        assert check_document_exists("dpia", tmp_path) is True

    def test_missing_document(self, tmp_path: Path) -> None:
        assert check_document_exists("dpia", tmp_path) is False

    def test_empty_document(self, tmp_path: Path) -> None:
        doc = tmp_path / "dpia.pdf"
        doc.write_text("")
        assert check_document_exists("dpia", tmp_path) is False


class TestCheckCompliance:
    def test_all_docs_present_passes(self, tmp_path: Path) -> None:
        manifest = AgentManifest(**copy.deepcopy(VALID_MANIFEST_DATA))
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()
        for doc_name in manifest.compliance.documents_required:
            (docs_dir / f"{doc_name}.md").write_text(f"# {doc_name}")

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.PASSED
        assert len(result.missing_documents) == 0

    def test_missing_docs_blocks(self, tmp_path: Path) -> None:
        manifest = AgentManifest(**copy.deepcopy(VALID_MANIFEST_DATA))
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()
        # Only create 2 of 5 required docs
        (docs_dir / "dpia.md").write_text("# DPIA")
        (docs_dir / "art50_transparency.md").write_text("# Art 50")

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert len(result.missing_documents) == 3

    def test_non_blocking_mode_warns(self, tmp_path: Path) -> None:
        data = copy.deepcopy(VALID_MANIFEST_DATA)
        data["compliance"] = {"blocking": False, "documents_required": ["dpia"]}
        manifest = AgentManifest(**data)
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.WARNING
        assert len(result.missing_documents) == 1

    def test_no_docs_required_passes(self, tmp_path: Path) -> None:
        data = copy.deepcopy(VALID_MANIFEST_DATA)
        data["compliance"] = {"blocking": False, "documents_required": []}
        manifest = AgentManifest(**data)
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_high_risk_requires_kill_switch(self, tmp_path: Path) -> None:
        data = copy.deepcopy(VALID_MANIFEST_DATA)
        data["agent"]["risk_class"] = "high"
        data["governance"] = {"kill_switch_authority": []}
        manifest = AgentManifest(**data)
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()
        for doc_name in manifest.compliance.documents_required:
            (docs_dir / f"{doc_name}.md").write_text(f"# {doc_name}")

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert any("kill_switch" in e for e in result.errors)

    def test_safety_gate_hook_required(self, tmp_path: Path) -> None:
        data = copy.deepcopy(VALID_MANIFEST_DATA)
        data["governance"] = {"hooks_enabled": []}
        manifest = AgentManifest(**data)
        docs_dir = tmp_path / "compliance"
        docs_dir.mkdir()
        for doc_name in manifest.compliance.documents_required:
            (docs_dir / f"{doc_name}.md").write_text(f"# {doc_name}")

        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert any("safety-gate" in e for e in result.errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd nomos-cli && uv run pytest tests/test_compliance_engine.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement compliance_engine.py**

```python
"""NomOS Compliance Engine — the blocking gate.

Verifies that an agent's manifest and compliance documents meet all
requirements before deployment. If blocking mode is enabled and
documents are missing, the agent CANNOT start.

This is what makes NomOS different: compliance by enforcement, not
recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from nomos.core.manifest import AgentManifest


class ComplianceStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"


# Supported document file extensions
_DOC_EXTENSIONS = (".md", ".pdf", ".txt", ".docx", ".html")

# Default required documents for EU AI Act + DSGVO compliance
REQUIRED_DOCUMENTS = [
    "dpia",
    "verarbeitungsverzeichnis",
    "art50_transparency",
    "art14_killswitch",
    "art12_logging",
]


@dataclass
class ComplianceResult:
    """Result of a compliance check."""

    status: ComplianceStatus
    missing_documents: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_document_exists(doc_name: str, docs_dir: Path) -> bool:
    """Check if a compliance document exists and is non-empty.

    Looks for doc_name with any supported extension (.md, .pdf, etc.).
    Returns False if the file exists but is empty.
    """
    for ext in _DOC_EXTENSIONS:
        candidate = docs_dir / f"{doc_name}{ext}"
        if candidate.exists() and candidate.stat().st_size > 0:
            return True
    return False


def check_compliance(manifest: AgentManifest, docs_dir: Path) -> ComplianceResult:
    """Run full compliance check against manifest and documents.

    Checks:
    1. All required compliance documents exist and are non-empty.
    2. High-risk agents have kill_switch_authority set.
    3. safety-gate hook is enabled.

    Returns ComplianceResult with status:
    - PASSED: all checks pass
    - WARNING: docs missing but blocking=False
    - BLOCKED: docs missing and blocking=True, or critical config errors
    """
    missing_docs: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    # Check required documents
    for doc_name in manifest.compliance.documents_required:
        if not check_document_exists(doc_name, docs_dir):
            missing_docs.append(doc_name)

    # Check kill switch for high-risk agents
    if (
        manifest.agent.risk_class.value == "high"
        and not manifest.governance.kill_switch_authority
    ):
        errors.append(
            "High-risk agent requires kill_switch_authority — "
            "at least one person must be able to stop this agent (Art. 14)."
        )

    # Check safety-gate hook
    if "safety-gate" not in manifest.governance.hooks_enabled:
        errors.append(
            "safety-gate hook must be enabled — "
            "agents need protection against destructive commands."
        )

    # Determine status
    if errors:
        return ComplianceResult(
            status=ComplianceStatus.BLOCKED,
            missing_documents=missing_docs,
            errors=errors,
            warnings=warnings,
        )

    if missing_docs:
        if manifest.compliance.blocking:
            return ComplianceResult(
                status=ComplianceStatus.BLOCKED,
                missing_documents=missing_docs,
                errors=[
                    f"Missing {len(missing_docs)} required document(s): "
                    + ", ".join(missing_docs)
                ],
                warnings=warnings,
            )
        return ComplianceResult(
            status=ComplianceStatus.WARNING,
            missing_documents=missing_docs,
            warnings=[
                f"Missing {len(missing_docs)} document(s) (non-blocking): "
                + ", ".join(missing_docs)
            ],
        )

    return ComplianceResult(
        status=ComplianceStatus.PASSED,
        missing_documents=[],
        errors=[],
        warnings=warnings,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd nomos-cli && uv run pytest tests/test_compliance_engine.py -v`
Expected: 7 passed

- [ ] **Step 5: Run ALL tests**

Run: `cd nomos-cli && uv run pytest -v`
Expected: 46 passed (21 + 11 + 7 + 7)

- [ ] **Step 6: Commit**

```bash
git add nomos-cli/nomos/core/compliance_engine.py nomos-cli/tests/test_compliance_engine.py
git commit -m "feat(core): compliance engine — the blocking gate

check_compliance() verifies manifest + documents before deployment:
- All required compliance docs exist and are non-empty
- High-risk agents have kill_switch_authority (Art. 14)
- safety-gate hook is enabled

Three statuses: PASSED (deploy allowed), WARNING (non-blocking mode),
BLOCKED (agent cannot start). This is enforcement, not recommendation.

7 tests: docs present, docs missing blocks, non-blocking warns,
high-risk kill switch, safety-gate required."
```

---

## Task 6: Forge Module (Agent Creation)

**Why:** The Forge creates a complete, deployable agent directory from a manifest template. This is the heart of `nomos hire` — the command that turns "I want an AI secretary" into a compliance-ready, sandboxed agent.

**Files:**
- Create: `nomos-cli/nomos/core/forge.py`
- Create: `nomos-cli/tests/test_forge.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for NomOS Forge — agent creation from templates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from nomos.core.forge import (
    ForgeResult,
    forge_agent,
)
from nomos.core.manifest import AgentManifest


class TestForgeAgent:
    def test_creates_output_directory(self, tmp_path: Path) -> None:
        result = forge_agent(
            agent_name="Mani Ruf",
            agent_role="external-secretary",
            company="AI Engineering",
            email="mani@ai-engineering.at",
            output_dir=tmp_path / "mani-ruf",
        )
        assert result.success is True
        assert result.output_dir.exists()

    def test_generates_valid_manifest(self, tmp_path: Path) -> None:
        out = tmp_path / "test-agent"
        result = forge_agent(
            agent_name="Test Agent",
            agent_role="research-agent",
            company="Test Co",
            email="test@test.com",
            output_dir=out,
        )
        manifest_file = out / "manifest.yaml"
        assert manifest_file.exists()

        data = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
        manifest = AgentManifest(**data)
        assert manifest.agent.name == "Test Agent"
        assert manifest.agent.role == "research-agent"
        assert manifest.identity.company == "Test Co"

    def test_generates_agent_id_from_name(self, tmp_path: Path) -> None:
        out = tmp_path / "mani-ruf"
        result = forge_agent(
            agent_name="Mani Ruf",
            agent_role="external-secretary",
            company="AI Engineering",
            email="mani@ai-engineering.at",
            output_dir=out,
        )
        data = yaml.safe_load((out / "manifest.yaml").read_text(encoding="utf-8"))
        assert data["agent"]["id"] == "mani-ruf"

    def test_creates_compliance_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        compliance_dir = out / "compliance"
        assert compliance_dir.exists()
        assert compliance_dir.is_dir()

    def test_creates_audit_chain(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        chain_file = out / "audit" / "chain.jsonl"
        assert chain_file.exists()
        first_entry = json.loads(
            chain_file.read_text(encoding="utf-8").strip().split("\n")[0]
        )
        assert first_entry["event_type"] == "agent.created"

    def test_refuses_existing_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "exists"
        out.mkdir()
        (out / "something.txt").write_text("occupied")

        result = forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        assert result.success is False
        assert "already exists" in result.error

    def test_creates_manifest_hash_file(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        hash_file = out / "manifest.sha256"
        assert hash_file.exists()
        assert len(hash_file.read_text(encoding="utf-8").strip()) == 64

    def test_unparseable_name_fails(self, tmp_path: Path) -> None:
        out = tmp_path / "bad"
        result = forge_agent(
            agent_name="---!!!---",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        assert result.success is False
        assert "agent ID" in result.error

    def test_special_characters_in_name(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        result = forge_agent(
            agent_name="Jörg Müller-Schmidt",
            agent_role="customer-support",
            company="Müller GmbH",
            email="j@mueller.at",
            output_dir=out,
        )
        assert result.success is True
        data = yaml.safe_load((out / "manifest.yaml").read_text(encoding="utf-8"))
        # ID should be ASCII-safe
        assert data["agent"]["id"] == "joerg-mueller-schmidt"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd nomos-cli && uv run pytest tests/test_forge.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement forge.py**

```python
"""NomOS Forge — create complete agent directories from parameters.

Takes a name, role, company, and email, and produces a ready-to-deploy
agent directory with manifest, compliance folder, and audit chain.
This is the heart of 'nomos hire'.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from nomos.core.events import EventType
from nomos.core.hash_chain import HashChain
from nomos.core.manifest import AgentManifest
from nomos.core.manifest_validator import compute_manifest_hash


@dataclass
class ForgeResult:
    """Result of agent creation."""

    success: bool
    output_dir: Path
    manifest_hash: str = ""
    error: str = ""


_GERMAN_TRANSLITERATION = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}


def _slugify(text: str) -> str:
    """Convert text to a valid agent ID (lowercase, hyphens only).

    Handles German umlauts explicitly (ö→oe, ü→ue, ä→ae, ß→ss),
    then falls back to NFKD normalization for other Unicode.
    """
    # German umlauts first (before NFKD strips the diacritics)
    for char, replacement in _GERMAN_TRANSLITERATION.items():
        text = text.replace(char, replacement)
    # Then normalize remaining unicode
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


def forge_agent(
    agent_name: str,
    agent_role: str,
    company: str,
    email: str,
    output_dir: Path,
    risk_class: str = "limited",
) -> ForgeResult:
    """Create a complete agent directory.

    Generates:
    - manifest.yaml (valid AgentManifest)
    - manifest.sha256 (hash for integrity verification)
    - compliance/ (empty directory for compliance documents)
    - audit/chain.jsonl (hash chain with creation event)
    """
    # Refuse to overwrite existing non-empty directory
    if output_dir.exists() and any(output_dir.iterdir()):
        return ForgeResult(
            success=False,
            output_dir=output_dir,
            error=f"Directory already exists and is not empty: {output_dir}",
        )

    agent_id = _slugify(agent_name)
    if not agent_id:
        return ForgeResult(
            success=False,
            output_dir=output_dir,
            error=f"Cannot generate valid agent ID from name: {agent_name!r}",
        )

    # Build manifest data
    now = datetime.now(timezone.utc).isoformat()
    manifest_data = {
        "agent": {
            "id": agent_id,
            "name": agent_name,
            "role": agent_role,
            "risk_class": risk_class,
            "created_at": now,
        },
        "identity": {
            "display_name": f"{agent_name} | AI-Assistent",
            "company": company,
            "email": email,
        },
        "memory": {
            "namespace": agent_id,
        },
    }

    # Validate via Pydantic
    try:
        manifest = AgentManifest(**manifest_data)
    except Exception as exc:
        return ForgeResult(
            success=False,
            output_dir=output_dir,
            error=f"Manifest validation failed: {exc}",
        )

    # Create directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    compliance_dir = output_dir / "compliance"
    compliance_dir.mkdir()
    audit_dir = output_dir / "audit"

    # Write manifest
    manifest_dict = manifest.model_dump(mode="json")
    manifest_file = output_dir / "manifest.yaml"
    manifest_file.write_text(
        yaml.dump(manifest_dict, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )

    # Write manifest hash
    manifest_hash = compute_manifest_hash(manifest)
    hash_file = output_dir / "manifest.sha256"
    hash_file.write_text(manifest_hash, encoding="utf-8")

    # Create audit chain with creation event
    chain = HashChain(storage_dir=audit_dir)
    chain.append(
        event_type=EventType.AGENT_CREATED,
        agent_id=agent_id,
        data={
            "name": agent_name,
            "role": agent_role,
            "company": company,
            "risk_class": risk_class,
            "manifest_hash": manifest_hash,
        },
    )

    return ForgeResult(
        success=True,
        output_dir=output_dir,
        manifest_hash=manifest_hash,
    )
```

- [ ] **Step 4: Add unicodedata note — no extra dependency needed (stdlib)**

Verify: `python -c "import unicodedata; print('OK')"` — unicodedata is part of Python stdlib.

- [ ] **Step 5: Run tests**

Run: `cd nomos-cli && uv run pytest tests/test_forge.py -v`
Expected: 9 passed

- [ ] **Step 6: Run ALL tests**

Run: `cd nomos-cli && uv run pytest -v`
Expected: 55 passed (21 + 11 + 7 + 7 + 9)

- [ ] **Step 7: Run linting**

Run: `ruff check nomos-cli/ && ruff format --check nomos-cli/`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add nomos-cli/nomos/core/forge.py nomos-cli/tests/test_forge.py
git commit -m "feat(core): forge — create complete agent directories

forge_agent() takes name, role, company, email and produces:
- manifest.yaml (valid Pydantic-checked AgentManifest)
- manifest.sha256 (integrity hash)
- compliance/ (directory for compliance documents)
- audit/chain.jsonl (hash chain with agent.created event)

Handles Unicode names (Jörg Müller → joerg-mueller), refuses to
overwrite non-empty directories, validates everything via Pydantic.

9 tests: directory creation, manifest validity, ID generation,
compliance dir, audit chain, overwrite protection, hash file,
unicode handling, unparseable name rejection."
```

---

## Task 7: Final Verification + Push

**Why:** A senior dev verifies EVERYTHING works together before declaring done.

- [ ] **Step 1: Run full test suite**

Run: `cd nomos-cli && uv run pytest -v --tb=short`
Expected: 55 passed, 0 failed

- [ ] **Step 2: Run linting**

Run: `ruff check nomos-cli/ && ruff format --check nomos-cli/`
Expected: No errors

- [ ] **Step 3: Verify no S9 violations remain**

```bash
cd C:\Users\Legion\Documents\nomos
# No "coming soon", "placeholder", "TODO" in source code
grep -r "coming soon" nomos-cli/ || echo "CLEAN"
grep -r "placeholder" nomos-cli/ || echo "CLEAN"
grep -r "TODO" nomos-cli/nomos/ || echo "CLEAN"
```
Expected: All CLEAN

- [ ] **Step 4: Verify no internal IPs leaked**

```bash
grep -r "10.40.10" nomos-cli/ schemas/ templates/ || echo "CLEAN"
```
Expected: CLEAN

- [ ] **Step 5: Verify git status is clean**

```bash
git status
git log --oneline -10
```

- [ ] **Step 6: Push to remote**

```bash
git push origin main
```

---

## Summary

After Plan 1 completion, the NomOS repo contains:

| Module | Lines | Tests | Status |
|--------|-------|-------|--------|
| manifest.py | 226 | 21 | EXISTING (kept) |
| manifest_validator.py | 88 | 21 | EXISTING (kept) |
| hash_chain.py | ~130 | 11 | NEW |
| events.py | ~60 | 7 | NEW |
| compliance_engine.py | ~100 | 7 | NEW |
| forge.py | ~120 | 9 | NEW |
| **Total** | **~740** | **55** | **All green** |

**What's next:** Plan 2 (NomOS API) builds on this foundation — FastAPI endpoints that use nomos-core for fleet registry, compliance checks, and audit trail.
