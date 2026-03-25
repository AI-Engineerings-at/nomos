"""Tests for BudgetConfig and ApprovalConfig extensions to AgentManifest."""

from __future__ import annotations

import copy

from nomos.core.manifest import AgentManifest, BudgetConfig, ApprovalConfig


def _valid_manifest_data() -> dict:
    """Minimal valid manifest data matching existing schema."""
    return {
        "agent": {
            "id": "mani-ruf-01",
            "name": "Mani Ruf",
            "role": "external-secretary",
            "risk_class": "limited",
            "created_at": "2026-03-23T00:00:00Z",
            "manifest_version": "1.0.0",
        },
        "identity": {
            "display_name": "Mani Ruf | AI-Assistent",
            "company": "Phantom AI GmbH",
            "email": "mani@phantom-ai.de",
            "ai_disclosure": "Diese Nachricht wurde mit KI-Unterstuetzung erstellt.",
        },
    }


def test_budget_config_defaults():
    budget = BudgetConfig()
    assert budget.monthly_limit_eur == 50.0
    assert budget.warn_at_percent == 80
    assert budget.auto_pause is True


def test_approval_config():
    approval = ApprovalConfig(
        required_for=["external_api_calls", "file_deletion", "data_export"]
    )
    assert len(approval.required_for) == 3


def test_approval_config_defaults():
    approval = ApprovalConfig()
    assert "external_api_calls" in approval.required_for
    assert approval.timeout_minutes == 60


def test_manifest_with_budget():
    data = _valid_manifest_data()
    data["budget"] = {"monthly_limit_eur": 100, "warn_at_percent": 90}
    manifest = AgentManifest(**data)
    assert manifest.budget.monthly_limit_eur == 100


def test_manifest_without_budget_gets_defaults():
    data = _valid_manifest_data()
    manifest = AgentManifest(**data)
    assert manifest.budget.monthly_limit_eur == 50.0


def test_manifest_without_approval_gets_defaults():
    data = _valid_manifest_data()
    manifest = AgentManifest(**data)
    assert manifest.approval.timeout_minutes == 60


def test_manifest_with_approval():
    data = _valid_manifest_data()
    data["approval"] = {"required_for": ["file_deletion"], "timeout_minutes": 30}
    manifest = AgentManifest(**data)
    assert manifest.approval.required_for == ["file_deletion"]
    assert manifest.approval.timeout_minutes == 30
