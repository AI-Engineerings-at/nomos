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

# German umlaut transliteration — applied BEFORE NFKD normalization
# so that ö→oe, ü→ue, ä→ae, ß→ss are preserved correctly.
_GERMAN_TRANSLITERATION = {
    "\u00e4": "ae",  # ä
    "\u00f6": "oe",  # ö
    "\u00fc": "ue",  # ü
    "\u00df": "ss",  # ß
    "\u00c4": "Ae",  # Ä
    "\u00d6": "Oe",  # Ö
    "\u00dc": "Ue",  # Ü
}


@dataclass
class ForgeResult:
    """Result of agent creation."""

    success: bool
    output_dir: Path
    manifest_hash: str = ""
    error: str = ""


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
