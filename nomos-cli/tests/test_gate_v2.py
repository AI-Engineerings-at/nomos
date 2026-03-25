"""Tests for NomOS Compliance Gate v2 — 14 documents for high-risk agents."""

from __future__ import annotations

from pathlib import Path

import pytest

from nomos.core.forge import forge_agent
from nomos.core.gate import generate_compliance_docs, REQUIRED_DOCS_V2
from nomos.core.manifest_validator import load_manifest


@pytest.fixture
def high_risk_agent_dir(tmp_path: Path) -> Path:
    """Create a high-risk agent directory for testing."""
    out = tmp_path / "high-risk-agent"
    forge_agent(
        agent_name="High Risk Agent",
        agent_role="automated-decision-maker",
        company="Test GmbH",
        email="test@test.at",
        output_dir=out,
        risk_class="high",
    )
    return out


@pytest.fixture
def limited_risk_agent_dir(tmp_path: Path) -> Path:
    """Create a limited-risk agent directory for testing."""
    out = tmp_path / "limited-risk-agent"
    forge_agent(
        agent_name="Limited Risk Agent",
        agent_role="external-secretary",
        company="Test GmbH",
        email="test@test.at",
        output_dir=out,
        risk_class="limited",
    )
    return out


@pytest.fixture
def minimal_risk_agent_dir(tmp_path: Path) -> Path:
    """Create a minimal-risk agent directory for testing."""
    out = tmp_path / "minimal-agent"
    forge_agent(
        agent_name="Minimal Agent",
        agent_role="chatbot",
        company="Test GmbH",
        email="test@test.at",
        output_dir=out,
        risk_class="minimal",
    )
    return out


class TestGateV2DocCount:
    def test_v2_registry_has_14_docs(self) -> None:
        assert len(REQUIRED_DOCS_V2) == 14

    def test_v2_doc_names(self) -> None:
        assert "dpia" in REQUIRED_DOCS_V2
        assert "avv" in REQUIRED_DOCS_V2
        assert "risk_management" in REQUIRED_DOCS_V2
        assert "tia" in REQUIRED_DOCS_V2
        assert "incident_response" in REQUIRED_DOCS_V2
        assert "tom" in REQUIRED_DOCS_V2
        assert "accessibility" in REQUIRED_DOCS_V2

    def test_high_risk_generates_13_docs_eu(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance")
        assert len(docs) == 13  # high risk EU = 13 (no TIA)

    def test_high_risk_generates_14_docs_us(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance", llm_location="us")
        assert len(docs) == 14  # high risk US = 14 (with TIA)

    def test_limited_risk_gets_9_docs(self, limited_risk_agent_dir: Path) -> None:
        manifest = load_manifest(limited_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, limited_risk_agent_dir / "compliance")
        assert len(docs) == 9

    def test_minimal_risk_gets_5_docs(self, minimal_risk_agent_dir: Path) -> None:
        manifest = load_manifest(minimal_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, minimal_risk_agent_dir / "compliance")
        assert len(docs) == 5


class TestGateV2Content:
    def test_each_doc_has_content(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance")
        for doc in docs:
            content = doc.path.read_text(encoding="utf-8")
            assert len(content) > 100, f"Doc {doc.name} is too short"

    def test_docs_contain_disclaimer(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance")
        for doc in docs:
            content = doc.path.read_text(encoding="utf-8")
            assert "NomOS" in content, f"Doc {doc.name} missing NomOS reference"
            assert "ersetzt keine" in content, f"Doc {doc.name} missing disclaimer"

    def test_docs_are_markdown(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance")
        for doc in docs:
            content = doc.path.read_text(encoding="utf-8")
            assert content.startswith("#"), f"Doc {doc.name} is not markdown"


class TestGateV2TIA:
    def test_us_location_generates_tia(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance", llm_location="us")
        doc_names = [d.name for d in docs]
        assert "tia" in doc_names

    def test_eu_location_skips_tia(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance", llm_location="eu")
        doc_names = [d.name for d in docs]
        assert "tia" not in doc_names

    def test_default_location_skips_tia(self, high_risk_agent_dir: Path) -> None:
        manifest = load_manifest(high_risk_agent_dir / "manifest.yaml")
        docs = generate_compliance_docs(manifest, high_risk_agent_dir / "compliance")
        doc_names = [d.name for d in docs]
        assert "tia" not in doc_names
