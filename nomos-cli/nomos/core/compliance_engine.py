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


_DOC_EXTENSIONS = (".md", ".pdf", ".txt", ".docx", ".html")

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
    """Check if a compliance document exists and is non-empty."""
    for ext in _DOC_EXTENSIONS:
        candidate = docs_dir / f"{doc_name}{ext}"
        if candidate.exists() and candidate.stat().st_size > 0:
            return True
    return False


def check_compliance(manifest: AgentManifest, docs_dir: Path) -> ComplianceResult:
    """Run full compliance check against manifest and documents."""
    missing_docs: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    for doc_name in manifest.compliance.documents_required:
        if not check_document_exists(doc_name, docs_dir):
            missing_docs.append(doc_name)

    if manifest.agent.risk_class.value == "high" and not manifest.governance.kill_switch_authority:
        errors.append(
            "High-risk agent requires kill_switch_authority — "
            "at least one person must be able to stop this agent (Art. 14)."
        )

    if "safety-gate" not in manifest.governance.hooks_enabled:
        errors.append("safety-gate hook must be enabled — agents need protection against destructive commands.")

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
                errors=[f"Missing {len(missing_docs)} required document(s): " + ", ".join(missing_docs)],
                warnings=warnings,
            )
        return ComplianceResult(
            status=ComplianceStatus.WARNING,
            missing_documents=missing_docs,
            warnings=[f"Missing {len(missing_docs)} document(s) (non-blocking): " + ", ".join(missing_docs)],
        )

    return ComplianceResult(
        status=ComplianceStatus.PASSED,
        missing_documents=[],
        errors=[],
        warnings=warnings,
    )
