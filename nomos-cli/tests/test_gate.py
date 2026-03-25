"""Tests for NomOS Compliance Gate — document generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from nomos.core.forge import forge_agent
from nomos.core.gate import generate_compliance_docs, load_compliance_status
from nomos.core.manifest_validator import load_manifest
from nomos.core.compliance_engine import check_compliance, ComplianceStatus


@pytest.fixture
def agent_dir(tmp_path: Path) -> Path:
    """Create a forged agent for testing."""
    out = tmp_path / "test-agent"
    forge_agent(
        agent_name="Test Agent",
        agent_role="external-secretary",
        company="Test GmbH",
        email="test@test.at",
        output_dir=out,
    )
    return out


class TestGenerateComplianceDocs:
    def test_generates_all_9_documents_for_limited_risk(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        assert len(docs) == 9  # limited risk gets 9 docs in Gate v2
        for doc in docs:
            assert doc.path.exists()
            assert doc.path.stat().st_size > 0

    def test_documents_contain_agent_info(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        dpia = next(d for d in docs if d.name == "dpia")
        content = dpia.path.read_text(encoding="utf-8")
        assert "Test Agent" in content
        assert "Test GmbH" in content

    def test_compliance_passes_after_generation(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        # Before: compliance should be blocked (no docs)
        result_before = check_compliance(manifest, agent_dir / "compliance")
        assert result_before.status == ComplianceStatus.BLOCKED

        # Generate docs
        generate_compliance_docs(manifest, agent_dir / "compliance")

        # After: compliance should pass
        result_after = check_compliance(manifest, agent_dir / "compliance")
        assert result_after.status == ComplianceStatus.PASSED

    def test_each_document_has_correct_name(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        names = {d.name for d in docs}
        expected = {
            "dpia", "verarbeitungsverzeichnis", "art50_transparency",
            "art14_killswitch", "art12_logging",
            "avv", "risk_management", "betroffenenrechte", "ai_literacy",
        }
        assert names == expected

    def test_documents_are_markdown(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        for doc in docs:
            assert doc.path.suffix == ".md"
            content = doc.path.read_text(encoding="utf-8")
            assert content.startswith("#")  # Markdown heading

    def test_dpia_contains_required_sections(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        dpia = next(d for d in docs if d.name == "dpia")
        content = dpia.path.read_text(encoding="utf-8")
        # DPIA must contain these sections per Art. 35 DSGVO
        assert "Verarbeitungszweck" in content or "Processing Purpose" in content
        assert "Risikobewertung" in content or "Risk Assessment" in content
        assert "Massnahmen" in content or "Measures" in content

    def test_art50_contains_ai_disclosure(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        art50 = next(d for d in docs if d.name == "art50_transparency")
        content = art50.path.read_text(encoding="utf-8")
        assert manifest.identity.ai_disclosure in content

    def test_art14_contains_killswitch_info(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, agent_dir / "compliance")
        art14 = next(d for d in docs if d.name == "art14_killswitch")
        content = art14.path.read_text(encoding="utf-8")
        assert "kill" in content.lower() or "oversight" in content.lower() or "halt" in content.lower()


class TestLoadComplianceStatus:
    def test_status_before_docs(self, agent_dir: Path) -> None:
        status = load_compliance_status(agent_dir)
        assert status["complete"] is False
        assert status["total"] == 9  # limited risk has 9 docs in Gate v2
        assert status["generated"] == 0

    def test_status_after_docs(self, agent_dir: Path) -> None:
        manifest = load_manifest(agent_dir / "manifest.yaml")
        generate_compliance_docs(manifest, agent_dir / "compliance")
        status = load_compliance_status(agent_dir)
        assert status["complete"] is True
        assert status["generated"] == 9  # limited risk has 9 docs in Gate v2
