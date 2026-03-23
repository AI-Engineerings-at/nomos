"""NomOS Manifest Validator — load, validate, and hash agent manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from nomos.core.manifest import AgentManifest


def load_manifest(path: Path) -> AgentManifest:
    """Load and parse an agent manifest from a YAML file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML is invalid or does not match the schema.
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a YAML mapping, got {type(data).__name__}")

    try:
        return AgentManifest(**data)
    except ValidationError as exc:
        raise ValueError(f"Manifest validation failed:\n{exc}") from exc


def validate_manifest(manifest: AgentManifest) -> list[str]:
    """Run additional business-rule checks beyond Pydantic schema validation.

    Returns a list of human-readable error strings.  An empty list means
    the manifest is fully valid.
    """
    errors: list[str] = []

    # Kill-switch authority must not be empty for high-risk agents
    if manifest.agent.risk_class.value == "high" and not manifest.governance.kill_switch_authority:
        errors.append("High-risk agents require at least one kill_switch_authority entry.")

    # Namespace should be set (or will be auto-generated — warn)
    if not manifest.memory.namespace:
        errors.append("memory.namespace is empty; it will be auto-generated from agent.id at runtime.")

    # Compliance docs must not be empty when blocking is enabled
    if manifest.compliance.blocking and not manifest.compliance.documents_required:
        errors.append("compliance.blocking is true but documents_required is empty.")

    # Governance hooks should include safety-gate at minimum
    if "safety-gate" not in manifest.governance.hooks_enabled:
        errors.append("governance.hooks_enabled should include 'safety-gate'.")

    return errors


def compute_manifest_hash(manifest: AgentManifest) -> str:
    """Compute a deterministic SHA-256 hash of the manifest.

    Uses the canonical JSON representation (sorted keys, no whitespace
    beyond separators) so that the hash is stable across platforms.
    """
    canonical = json.dumps(
        manifest.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
