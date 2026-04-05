"""Tests for risk-class-aware compliance checking (5 to 14 documents).

TASK-00546: The compliance engine must check documents based on the
agent's risk_class, not just the hardcoded 5. Gate v2 defines up to
14 documents depending on risk class and LLM location.
"""

from __future__ import annotations

import copy
from pathlib import Path

from nomos.core.compliance_engine import (
    ComplianceStatus,
    check_compliance,
    get_required_documents,
)
from nomos.core.gate import (
    DOCS_FOR_RISK,
    generate_compliance_docs,
    get_docs_for_risk,
)
from nomos.core.manifest import AgentManifest


# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

_BASE_MANIFEST: dict = {
    "agent": {
        "id": "compliance-test",
        "name": "Compliance Test Agent",
        "role": "test-role",
        "created_at": "2026-03-31T00:00:00Z",
    },
    "identity": {
        "display_name": "Compliance Test",
        "company": "Test GmbH",
        "email": "test@test.com",
    },
}


def _manifest(risk_class: str = "minimal", docs_required: list[str] | None = None) -> AgentManifest:
    """Create a manifest with the given risk class."""
    data = copy.deepcopy(_BASE_MANIFEST)
    data["agent"]["risk_class"] = risk_class
    if docs_required is not None:
        data["compliance"] = {"documents_required": docs_required}
    return AgentManifest(**data)


def _create_docs(docs_dir: Path, doc_names: list[str]) -> None:
    """Create dummy compliance documents in docs_dir."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in doc_names:
        (docs_dir / f"{name}.md").write_text(f"# {name}")


# ---------------------------------------------------------------------------
# Tests: get_docs_for_risk (public API from gate.py)
# ---------------------------------------------------------------------------


class TestGetDocsForRisk:
    def test_minimal_returns_5_docs(self) -> None:
        docs = get_docs_for_risk("minimal", "eu")
        assert len(docs) == 5

    def test_limited_returns_9_docs(self) -> None:
        docs = get_docs_for_risk("limited", "eu")
        assert len(docs) == 9

    def test_high_eu_returns_13_docs(self) -> None:
        docs = get_docs_for_risk("high", "eu")
        assert len(docs) == 13

    def test_high_us_returns_14_docs_with_tia(self) -> None:
        docs = get_docs_for_risk("high", "us")
        assert len(docs) == 14
        assert "tia" in docs

    def test_unknown_risk_falls_back_to_minimal(self) -> None:
        docs = get_docs_for_risk("unknown", "eu")
        assert len(docs) == 5

    def test_docs_for_risk_dict_is_public(self) -> None:
        assert "minimal" in DOCS_FOR_RISK
        assert "limited" in DOCS_FOR_RISK
        assert "high" in DOCS_FOR_RISK


# ---------------------------------------------------------------------------
# Tests: get_required_documents (compliance_engine)
# ---------------------------------------------------------------------------


class TestGetRequiredDocuments:
    def test_minimal_risk_returns_5(self) -> None:
        assert len(get_required_documents("minimal")) == 5

    def test_limited_risk_returns_9(self) -> None:
        assert len(get_required_documents("limited")) == 9

    def test_high_risk_eu_returns_13(self) -> None:
        assert len(get_required_documents("high", llm_location="eu")) == 13

    def test_high_risk_us_returns_14(self) -> None:
        docs = get_required_documents("high", llm_location="us")
        assert len(docs) == 14
        assert "tia" in docs


# ---------------------------------------------------------------------------
# Tests: check_compliance with risk-class-aware documents
# ---------------------------------------------------------------------------


class TestComplianceRiskClassAware:
    def test_minimal_5_present_passes(self, tmp_path: Path) -> None:
        """Minimal risk: 5 docs required, 5 present = PASSED."""
        required = get_required_documents("minimal")
        manifest = _manifest("minimal", docs_required=required)
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required)
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_minimal_3_present_blocks(self, tmp_path: Path) -> None:
        """Minimal risk: 5 docs required, only 3 present = BLOCKED."""
        required = get_required_documents("minimal")
        manifest = _manifest("minimal", docs_required=required)
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required[:3])
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert len(result.missing_documents) == 2

    def test_limited_5_present_blocks(self, tmp_path: Path) -> None:
        """Limited risk: 9 docs required, only 5 present = BLOCKED."""
        required = get_required_documents("limited")
        manifest = _manifest("limited", docs_required=required)
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required[:5])
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert len(result.missing_documents) == 4

    def test_limited_9_present_passes(self, tmp_path: Path) -> None:
        """Limited risk: 9 docs required, 9 present = PASSED."""
        required = get_required_documents("limited")
        manifest = _manifest("limited", docs_required=required)
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required)
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_high_9_present_blocks(self, tmp_path: Path) -> None:
        """High risk: 13 docs required, only 9 present = BLOCKED."""
        required = get_required_documents("high", llm_location="eu")
        manifest = _manifest("high", docs_required=required)
        # Need kill_switch_authority for high risk
        manifest.governance.kill_switch_authority = ["admin"]
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required[:9])
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.BLOCKED
        assert len(result.missing_documents) == 4

    def test_high_us_14_required(self, tmp_path: Path) -> None:
        """High risk + US LLM: 14 docs required (includes TIA)."""
        required = get_required_documents("high", llm_location="us")
        assert len(required) == 14
        assert "tia" in required
        manifest = _manifest("high", docs_required=required)
        manifest.governance.kill_switch_authority = ["admin"]
        docs_dir = tmp_path / "compliance"
        _create_docs(docs_dir, required)
        result = check_compliance(manifest, docs_dir)
        assert result.status == ComplianceStatus.PASSED


# ---------------------------------------------------------------------------
# Tests: Roundtrip — generate + check = PASSED for each risk class
# ---------------------------------------------------------------------------


class TestRoundtripGenerateAndCheck:
    def test_roundtrip_minimal(self, tmp_path: Path) -> None:
        manifest = _manifest("minimal")
        docs_dir = tmp_path / "compliance"
        generated = generate_compliance_docs(manifest, docs_dir)
        # Update manifest to require what was generated
        doc_names = [d.name for d in generated]
        manifest_with_docs = _manifest("minimal", docs_required=doc_names)
        result = check_compliance(manifest_with_docs, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_roundtrip_limited(self, tmp_path: Path) -> None:
        manifest = _manifest("limited")
        docs_dir = tmp_path / "compliance"
        generated = generate_compliance_docs(manifest, docs_dir)
        doc_names = [d.name for d in generated]
        manifest_with_docs = _manifest("limited", docs_required=doc_names)
        result = check_compliance(manifest_with_docs, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_roundtrip_high_eu(self, tmp_path: Path) -> None:
        manifest = _manifest("high")
        manifest.governance.kill_switch_authority = ["admin"]
        docs_dir = tmp_path / "compliance"
        generated = generate_compliance_docs(manifest, docs_dir, llm_location="eu")
        doc_names = [d.name for d in generated]
        manifest_with_docs = _manifest("high", docs_required=doc_names)
        manifest_with_docs.governance.kill_switch_authority = ["admin"]
        result = check_compliance(manifest_with_docs, docs_dir)
        assert result.status == ComplianceStatus.PASSED

    def test_roundtrip_high_us(self, tmp_path: Path) -> None:
        manifest = _manifest("high")
        manifest.governance.kill_switch_authority = ["admin"]
        docs_dir = tmp_path / "compliance"
        generated = generate_compliance_docs(manifest, docs_dir, llm_location="us")
        doc_names = [d.name for d in generated]
        manifest_with_docs = _manifest("high", docs_required=doc_names)
        manifest_with_docs.governance.kill_switch_authority = ["admin"]
        result = check_compliance(manifest_with_docs, docs_dir)
        assert result.status == ComplianceStatus.PASSED
        assert "tia" in doc_names
