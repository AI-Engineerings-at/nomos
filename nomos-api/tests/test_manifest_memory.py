"""Tests for MemoryConfig in AgentManifest."""

from __future__ import annotations

from nomos.core.manifest import (
    AgentManifest,
    MemoryConfig,
    IsolationLevel,
    MemoryBackend,
    PIIFilterConfig,
    DeriverConfig,
    RetentionConfig,
)


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


def test_memory_config_defaults():
    mem = MemoryConfig()
    assert mem.backend == MemoryBackend.local
    assert mem.namespace == ""
    assert mem.isolation_level == IsolationLevel.strict
    assert isinstance(mem.pii_filter, PIIFilterConfig)
    assert isinstance(mem.deriver, DeriverConfig)
    assert isinstance(mem.retention, RetentionConfig)


def test_memory_config_custom():
    mem = MemoryConfig(
        backend=MemoryBackend.honcho,
        namespace="mani",
        isolation_level=IsolationLevel.project,
    )
    assert mem.namespace == "mani"
    assert mem.backend == MemoryBackend.honcho
    assert mem.isolation_level == IsolationLevel.project


def test_manifest_with_memory():
    data = _valid_manifest_data()
    data["memory"] = {
        "backend": "honcho",
        "namespace": "mani",
        "isolation_level": "strict",
    }
    manifest = AgentManifest(**data)
    assert manifest.memory.namespace == "mani"
    assert manifest.memory.backend == MemoryBackend.honcho


def test_memory_isolation_values():
    for val in ["strict", "project", "shared"]:
        mem = MemoryConfig(isolation_level=val)
        assert mem.isolation_level == IsolationLevel(val)


def test_memory_retention_defaults():
    mem = MemoryConfig()
    assert mem.retention.session_messages_days == 90
    assert mem.retention.representations_days == 365
    assert mem.retention.audit_logs_days == 730


def test_memory_pii_filter_defaults():
    mem = MemoryConfig()
    assert mem.pii_filter.enabled is True
    assert mem.pii_filter.mask_emails is True
    assert mem.pii_filter.mask_phones is True


def test_manifest_without_memory_gets_defaults():
    data = _valid_manifest_data()
    manifest = AgentManifest(**data)
    assert manifest.memory.backend == MemoryBackend.local
    assert manifest.memory.isolation_level == IsolationLevel.strict
    assert manifest.memory.retention.session_messages_days == 90
