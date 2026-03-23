"""Tests for NomOS Compliance Engine — the blocking gate."""

from __future__ import annotations

import copy
from pathlib import Path


from nomos.core.compliance_engine import (
    ComplianceStatus,
    check_compliance,
    check_document_exists,
)
from nomos.core.manifest import AgentManifest


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
