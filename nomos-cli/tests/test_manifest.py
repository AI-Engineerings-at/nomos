"""Tests for NomOS Agent Manifest schema, validation, and hashing."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from nomos.core.manifest import AgentManifest
from nomos.core.manifest_validator import (
    compute_manifest_hash,
    load_manifest,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_MANIFEST_DATA: dict = {
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
    "nemoclaw": {
        "enabled": True,
        "sandbox_profile": "limited",
        "network_policy": "outbound-restricted",
        "credential_guard": True,
        "audit_logging": True,
    },
    "compliance": {
        "documents_required": [
            "dpia",
            "verarbeitungsverzeichnis",
            "art50_transparency",
            "art14_killswitch",
            "art12_logging",
        ],
        "sign_off_required": True,
        "blocking": True,
    },
    "governance": {
        "hooks_enabled": [
            "safety-gate",
            "quality-gate",
            "credential-guard",
            "kill-switch",
            "escalation-tracker",
            "audit-logger",
            "art50-labeler",
            "session-init",
        ],
        "kill_switch_authority": ["joe"],
        "escalation_threshold": 2,
        "audit_retention_days": 365,
    },
    "memory": {
        "backend": "honcho",
        "namespace": "mani-ruf-01",
        "isolation_level": "strict",
        "pii_filter": {
            "enabled": True,
            "mask_emails": True,
            "mask_phones": True,
            "mask_addresses": True,
            "keep_names": False,
        },
        "deriver": {
            "enabled": True,
            "review_mode": "auto",
        },
        "retention": {
            "session_messages_days": 90,
            "representations_days": 365,
            "audit_logs_days": 730,
        },
    },
    "multi_agent": {
        "inherits_rules_from": ["shared-base-rules"],
        "project_scope": "",
    },
    "skills": ["external-secretary"],
}


def _write_yaml(data: dict, path: Path) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


@pytest.fixture
def valid_data() -> dict:
    return copy.deepcopy(VALID_MANIFEST_DATA)


@pytest.fixture
def valid_manifest(valid_data: dict) -> AgentManifest:
    return AgentManifest(**valid_data)


@pytest.fixture
def valid_yaml_file(valid_data: dict, tmp_path: Path) -> Path:
    p = tmp_path / "manifest.yaml"
    _write_yaml(valid_data, p)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestValidManifest:
    def test_valid_manifest_loads(self, valid_yaml_file: Path) -> None:
        manifest = load_manifest(valid_yaml_file)
        assert manifest.agent.id == "mani-ruf-01"
        assert manifest.agent.name == "Mani Ruf"
        assert manifest.agent.risk_class.value == "limited"
        assert manifest.identity.company == "Phantom AI GmbH"
        assert manifest.nemoclaw.enabled is True
        assert "dpia" in manifest.compliance.documents_required
        assert "safety-gate" in manifest.governance.hooks_enabled
        assert manifest.memory.backend.value == "honcho"
        assert manifest.skills == ["external-secretary"]


class TestInvalidId:
    @pytest.mark.parametrize(
        "bad_id",
        [
            "../traversal",
            "has spaces",
            "UPPERCASE",
            "special!chars",
            "under_score",
            "dot.dot",
            "",
            "-leading-hyphen",
            "trailing-hyphen-",
        ],
    )
    def test_invalid_id_rejected(self, valid_data: dict, bad_id: str) -> None:
        valid_data["agent"]["id"] = bad_id
        with pytest.raises((ValueError, Exception)):
            AgentManifest(**valid_data)


class TestInvalidRiskClass:
    @pytest.mark.parametrize("bad_class", ["critical", "LOW", "unknown", ""])
    def test_invalid_risk_class_rejected(self, valid_data: dict, bad_class: str) -> None:
        valid_data["agent"]["risk_class"] = bad_class
        with pytest.raises((ValueError, Exception)):
            AgentManifest(**valid_data)


class TestExtraForbid:
    def test_unknown_fields_rejected(self, valid_data: dict) -> None:
        valid_data["agent"]["unknown_field"] = "surprise"
        with pytest.raises((ValueError, Exception)):
            AgentManifest(**valid_data)

    def test_unknown_top_level_field_rejected(self, valid_data: dict) -> None:
        valid_data["bonus_section"] = {"foo": "bar"}
        with pytest.raises((ValueError, Exception)):
            AgentManifest(**valid_data)


class TestDefaults:
    def test_default_values_applied(self) -> None:
        minimal = {
            "agent": {
                "id": "test-agent",
                "name": "Test Agent",
                "role": "research-agent",
                "created_at": "2026-01-01T00:00:00Z",
            },
            "identity": {
                "display_name": "Test Agent",
                "company": "Test Co",
                "email": "test@test.com",
            },
        }
        manifest = AgentManifest(**minimal)
        assert manifest.agent.risk_class.value == "limited"
        assert manifest.agent.manifest_version == "1.0.0"
        assert manifest.nemoclaw.enabled is True
        assert manifest.nemoclaw.sandbox_profile.value == "limited"
        assert manifest.compliance.blocking is True
        assert manifest.governance.escalation_threshold == 2
        assert manifest.memory.backend.value == "local"
        assert manifest.memory.isolation_level.value == "strict"
        assert manifest.memory.pii_filter.enabled is True
        assert manifest.memory.retention.audit_logs_days == 730
        assert manifest.identity.ai_disclosure == "Diese Nachricht wurde mit KI-Unterstuetzung erstellt."
        assert manifest.skills == []


class TestManifestHash:
    def test_manifest_hash_deterministic(self, valid_manifest: AgentManifest) -> None:
        h1 = compute_manifest_hash(valid_manifest)
        h2 = compute_manifest_hash(valid_manifest)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_manifest_hash_changes_on_edit(self, valid_data: dict) -> None:
        m1 = AgentManifest(**valid_data)
        h1 = compute_manifest_hash(m1)

        modified = copy.deepcopy(valid_data)
        modified["agent"]["name"] = "Different Name"
        m2 = AgentManifest(**modified)
        h2 = compute_manifest_hash(m2)

        assert h1 != h2


class TestEmptyManifest:
    def test_empty_manifest_fails(self) -> None:
        with pytest.raises((ValueError, Exception)):
            AgentManifest()  # type: ignore[call-arg]

    def test_empty_yaml_file_fails(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        with pytest.raises((ValueError, FileNotFoundError)):
            load_manifest(p)
