"""Tests for NomOS Forge — agent creation from templates."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from nomos.core.forge import (
    ForgeResult,  # noqa: F401 — imported for public API verification
    forge_agent,
)
from nomos.core.manifest import AgentManifest


class TestForgeAgent:
    def test_creates_output_directory(self, tmp_path: Path) -> None:
        result = forge_agent(
            agent_name="Mani Ruf",
            agent_role="external-secretary",
            company="AI Engineering",
            email="mani@ai-engineering.at",
            output_dir=tmp_path / "mani-ruf",
        )
        assert result.success is True
        assert result.output_dir.exists()

    def test_generates_valid_manifest(self, tmp_path: Path) -> None:
        out = tmp_path / "test-agent"
        forge_agent(
            agent_name="Test Agent",
            agent_role="research-agent",
            company="Test Co",
            email="test@test.com",
            output_dir=out,
        )
        manifest_file = out / "manifest.yaml"
        assert manifest_file.exists()
        data = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
        manifest = AgentManifest(**data)
        assert manifest.agent.name == "Test Agent"
        assert manifest.agent.role == "research-agent"
        assert manifest.identity.company == "Test Co"

    def test_generates_agent_id_from_name(self, tmp_path: Path) -> None:
        out = tmp_path / "mani-ruf"
        forge_agent(
            agent_name="Mani Ruf",
            agent_role="external-secretary",
            company="AI Engineering",
            email="mani@ai-engineering.at",
            output_dir=out,
        )
        data = yaml.safe_load((out / "manifest.yaml").read_text(encoding="utf-8"))
        assert data["agent"]["id"] == "mani-ruf"

    def test_creates_compliance_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        compliance_dir = out / "compliance"
        assert compliance_dir.exists()
        assert compliance_dir.is_dir()

    def test_creates_audit_chain(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        chain_file = out / "audit" / "chain.jsonl"
        assert chain_file.exists()
        first_entry = json.loads(chain_file.read_text(encoding="utf-8").strip().split("\n")[0])
        assert first_entry["event_type"] == "agent.created"

    def test_refuses_existing_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "exists"
        out.mkdir()
        (out / "something.txt").write_text("occupied")
        result = forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        assert result.success is False
        assert "already exists" in result.error

    def test_creates_manifest_hash_file(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        forge_agent(
            agent_name="Test",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        hash_file = out / "manifest.sha256"
        assert hash_file.exists()
        assert len(hash_file.read_text(encoding="utf-8").strip()) == 64

    def test_unparseable_name_fails(self, tmp_path: Path) -> None:
        out = tmp_path / "bad"
        result = forge_agent(
            agent_name="---!!!---",
            agent_role="test",
            company="Co",
            email="t@t.com",
            output_dir=out,
        )
        assert result.success is False
        assert "agent ID" in result.error

    def test_special_characters_in_name(self, tmp_path: Path) -> None:
        out = tmp_path / "test"
        result = forge_agent(
            agent_name="Joerg Mueller-Schmidt",
            agent_role="customer-support",
            company="Mueller GmbH",
            email="j@mueller.at",
            output_dir=out,
        )
        assert result.success is True
        data = yaml.safe_load((out / "manifest.yaml").read_text(encoding="utf-8"))
        assert data["agent"]["id"] == "joerg-mueller-schmidt"
