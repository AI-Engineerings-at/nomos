"""Tests for NomOS CLI commands."""

from __future__ import annotations

from pathlib import Path
from click.testing import CliRunner

import pytest

from nomos.cli import main
from nomos.core.forge import forge_agent


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def agents_dir(tmp_path: Path) -> Path:
    """Create a temp agents directory with one forged agent."""
    agent_dir = tmp_path / "test-agent"
    forge_agent(
        agent_name="Test Agent",
        agent_role="test-role",
        company="Test Co",
        email="test@test.com",
        output_dir=agent_dir,
    )
    return tmp_path


class TestHire:
    def test_hire_with_flags(self, runner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            [
                "hire",
                "--name",
                "Mani Ruf",
                "--role",
                "external-secretary",
                "--company",
                "AI Engineering",
                "--email",
                "mani@ai-engineering.at",
                "--output-dir",
                str(tmp_path / "mani-ruf"),
            ],
        )
        assert result.exit_code == 0
        assert "mani-ruf" in result.output.lower() or "created" in result.output.lower()
        assert (tmp_path / "mani-ruf" / "manifest.yaml").exists()

    def test_hire_creates_audit_chain(self, runner, tmp_path: Path) -> None:
        runner.invoke(
            main,
            [
                "hire",
                "--name",
                "Audit Agent",
                "--role",
                "test",
                "--company",
                "Co",
                "--email",
                "t@t.com",
                "--output-dir",
                str(tmp_path / "audit-agent"),
            ],
        )
        assert (tmp_path / "audit-agent" / "audit" / "chain.jsonl").exists()

    def test_hire_missing_required_flags(self, runner) -> None:
        result = runner.invoke(main, ["hire"])
        assert result.exit_code != 0


class TestVerify:
    def test_verify_agent(self, runner, agents_dir: Path) -> None:
        agent_dir = agents_dir / "test-agent"
        result = runner.invoke(main, ["verify", "--agent-dir", str(agent_dir)])
        assert result.exit_code == 0
        assert (
            "compliance" in result.output.lower()
            or "blocked" in result.output.lower()
            or "passed" in result.output.lower()
        )

    def test_verify_nonexistent_dir(self, runner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["verify", "--agent-dir", str(tmp_path / "nonexistent")])
        assert result.exit_code != 0


class TestFleet:
    def test_fleet_empty(self, runner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["fleet", "--agents-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "0" in result.output or "no agent" in result.output.lower() or "empty" in result.output.lower()

    def test_fleet_with_agents(self, runner, agents_dir: Path) -> None:
        result = runner.invoke(main, ["fleet", "--agents-dir", str(agents_dir)])
        assert result.exit_code == 0
        assert "test-agent" in result.output.lower()


class TestAudit:
    def test_audit_show(self, runner, agents_dir: Path) -> None:
        agent_dir = agents_dir / "test-agent"
        result = runner.invoke(main, ["audit", "--agent-dir", str(agent_dir)])
        assert result.exit_code == 0
        assert "agent.created" in result.output

    def test_audit_verify(self, runner, agents_dir: Path) -> None:
        agent_dir = agents_dir / "test-agent"
        result = runner.invoke(main, ["audit", "--agent-dir", str(agent_dir), "--verify"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "pass" in result.output.lower()


class TestVersion:
    def test_version(self, runner) -> None:
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
