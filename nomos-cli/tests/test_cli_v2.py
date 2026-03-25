"""Tests for CLI v2 commands (API-backed).

Each command has at least two tests: happy path + error case.
The API client is mocked — no running server required.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from nomos.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ── Helpers ──────────────────────────────────────────────────────────────

AGENT_RESPONSE = {
    "id": "mani-ruf-01",
    "name": "Mani Ruf",
    "role": "external-secretary",
    "company": "TestCo",
    "email": "mani@test.com",
    "risk_class": "limited",
    "status": "paused",
    "manifest_hash": "abc123",
    "compliance_status": "passed",
    "created_at": "2026-03-25T10:00:00",
}


def _ok(data: dict) -> dict:
    return {"success": True, "data": data}


def _err(msg: str, status_code: int = 404) -> dict:
    return {"success": False, "error": msg, "status_code": status_code}


# ═══════════════════════════════════════════════════════════════════════════
# 1. pause
# ═══════════════════════════════════════════════════════════════════════════


class TestPause:
    @patch("nomos.core.api.pause_agent")
    def test_pause_success(self, mock_pause, runner: CliRunner) -> None:
        mock_pause.return_value = _ok(AGENT_RESPONSE)
        result = runner.invoke(main, ["pause", "mani-ruf-01"])
        assert result.exit_code == 0
        assert "Mani Ruf" in result.output
        assert "pausiert" in result.output

    @patch("nomos.core.api.pause_agent")
    def test_pause_not_found(self, mock_pause, runner: CliRunner) -> None:
        mock_pause.return_value = _err("Agent 'mani-ruf-01' not found")
        result = runner.invoke(main, ["pause", "mani-ruf-01"])
        assert result.exit_code != 0
        assert "Fehler" in result.output

    @patch("nomos.core.api.pause_agent")
    def test_pause_json(self, mock_pause, runner: CliRunner) -> None:
        mock_pause.return_value = _ok(AGENT_RESPONSE)
        result = runner.invoke(main, ["pause", "--json", "mani-ruf-01"])
        assert result.exit_code == 0
        assert '"success": true' in result.output


# ═══════════════════════════════════════════════════════════════════════════
# 2. resume
# ═══════════════════════════════════════════════════════════════════════════


class TestResume:
    @patch("nomos.core.api.resume_agent")
    def test_resume_success(self, mock_resume, runner: CliRunner) -> None:
        data = {**AGENT_RESPONSE, "status": "running"}
        mock_resume.return_value = _ok(data)
        result = runner.invoke(main, ["resume", "mani-ruf-01"])
        assert result.exit_code == 0
        assert "laeuft wieder" in result.output

    @patch("nomos.core.api.resume_agent")
    def test_resume_conflict(self, mock_resume, runner: CliRunner) -> None:
        mock_resume.return_value = _err("Agent 'mani-ruf-01' is not paused", 409)
        result = runner.invoke(main, ["resume", "mani-ruf-01"])
        assert result.exit_code != 0
        assert "not paused" in result.output


# ═══════════════════════════════════════════════════════════════════════════
# 3. retire
# ═══════════════════════════════════════════════════════════════════════════


class TestRetire:
    @patch("nomos.core.api.retire_agent")
    def test_retire_success(self, mock_retire, runner: CliRunner) -> None:
        data = {**AGENT_RESPONSE, "status": "retired"}
        mock_retire.return_value = _ok(data)
        result = runner.invoke(main, ["retire", "mani-ruf-01"])
        assert result.exit_code == 0
        assert "Ruhestand" in result.output

    @patch("nomos.core.api.retire_agent")
    def test_retire_not_found(self, mock_retire, runner: CliRunner) -> None:
        mock_retire.return_value = _err("Agent 'xyz' not found")
        result = runner.invoke(main, ["retire", "xyz"])
        assert result.exit_code != 0
        assert "Fehler" in result.output


# ═══════════════════════════════════════════════════════════════════════════
# 4. forget
# ═══════════════════════════════════════════════════════════════════════════


class TestForget:
    @patch("nomos.core.api.forget_email")
    def test_forget_success(self, mock_forget, runner: CliRunner) -> None:
        mock_forget.return_value = _ok({
            "deleted_messages": 3,
            "search_term": "max@example.com",
            "audit_event": "dsgvo.forget",
            "audit_preserved": True,
            "timestamp": "2026-03-25T10:00:00Z",
        })
        result = runner.invoke(main, ["forget", "max@example.com"])
        assert result.exit_code == 0
        assert "3 Nachrichten" in result.output
        assert "max@example.com" in result.output

    @patch("nomos.core.api.forget_email")
    def test_forget_error(self, mock_forget, runner: CliRunner) -> None:
        mock_forget.return_value = _err("Ungueltige Anfrage", 400)
        result = runner.invoke(main, ["forget", "bad"])
        assert result.exit_code != 0
        assert "Fehler" in result.output


# ═══════════════════════════════════════════════════════════════════════════
# 5. assign
# ═══════════════════════════════════════════════════════════════════════════


class TestAssign:
    @patch("nomos.core.api.create_task")
    def test_assign_success(self, mock_create, runner: CliRunner) -> None:
        mock_create.return_value = _ok({
            "id": "task-001",
            "agent_id": "mani-ruf-01",
            "description": "Write blog post",
            "priority": "normal",
            "status": "queued",
            "timeout_minutes": 60,
            "created_at": "2026-03-25T10:00:00Z",
        })
        result = runner.invoke(main, ["assign", "mani-ruf-01", "--task", "Write blog post"])
        assert result.exit_code == 0
        assert "task-001" in result.output
        assert "Write blog post" in result.output

    @patch("nomos.core.api.create_task")
    def test_assign_error(self, mock_create, runner: CliRunner) -> None:
        mock_create.return_value = _err("Agent nicht gefunden", 404)
        result = runner.invoke(main, ["assign", "xyz", "--task", "something"])
        assert result.exit_code != 0
        assert "Fehler" in result.output

    @patch("nomos.core.api.create_task")
    def test_assign_with_priority(self, mock_create, runner: CliRunner) -> None:
        mock_create.return_value = _ok({
            "id": "task-002",
            "agent_id": "mani-ruf-01",
            "description": "Urgent task",
            "priority": "urgent",
            "status": "queued",
            "timeout_minutes": 30,
            "created_at": "2026-03-25T10:00:00Z",
        })
        result = runner.invoke(
            main,
            ["assign", "mani-ruf-01", "--task", "Urgent task", "--priority", "urgent", "--timeout", "30"],
        )
        assert result.exit_code == 0
        mock_create.assert_called_once_with("mani-ruf-01", "Urgent task", priority="urgent", timeout_minutes=30)


# ═══════════════════════════════════════════════════════════════════════════
# 6. costs (all agents)
# ═══════════════════════════════════════════════════════════════════════════


class TestCostsAll:
    @patch("nomos.core.api.get_costs")
    def test_costs_all_success(self, mock_costs, runner: CliRunner) -> None:
        mock_costs.return_value = _ok({
            "costs": [
                {
                    "agent_id": "mani-ruf-01",
                    "total_cost_eur": 12.50,
                    "budget_limit_eur": 50.0,
                    "budget_status": "ok",
                    "percent_used": 25.0,
                },
            ],
            "total": 1,
        })
        result = runner.invoke(main, ["costs"])
        assert result.exit_code == 0
        assert "mani-ruf-01" in result.output
        assert "12.50" in result.output

    @patch("nomos.core.api.get_costs")
    def test_costs_all_empty(self, mock_costs, runner: CliRunner) -> None:
        mock_costs.return_value = _ok({"costs": [], "total": 0})
        result = runner.invoke(main, ["costs"])
        assert result.exit_code == 0
        assert "Keine Kostendaten" in result.output

    @patch("nomos.core.api.get_costs")
    def test_costs_all_error(self, mock_costs, runner: CliRunner) -> None:
        mock_costs.return_value = _err("Interner Serverfehler", 500)
        result = runner.invoke(main, ["costs"])
        assert result.exit_code != 0


# ═══════════════════════════════════════════════════════════════════════════
# 7. costs <agent_id> (single agent)
# ═══════════════════════════════════════════════════════════════════════════


class TestCostsSingle:
    @patch("nomos.core.api.get_agent_costs")
    def test_costs_single_success(self, mock_costs, runner: CliRunner) -> None:
        mock_costs.return_value = _ok({
            "agent_id": "mani-ruf-01",
            "total_cost_eur": 12.50,
            "budget_limit_eur": 50.0,
            "budget_status": "ok",
            "percent_used": 25.0,
        })
        result = runner.invoke(main, ["costs", "mani-ruf-01"])
        assert result.exit_code == 0
        assert "mani-ruf-01" in result.output
        assert "12.50" in result.output

    @patch("nomos.core.api.get_agent_costs")
    def test_costs_single_not_found(self, mock_costs, runner: CliRunner) -> None:
        mock_costs.return_value = _err("Agent nicht gefunden", 404)
        result = runner.invoke(main, ["costs", "xyz"])
        assert result.exit_code != 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. incidents
# ═══════════════════════════════════════════════════════════════════════════


class TestIncidents:
    @patch("nomos.core.api.get_incidents")
    def test_incidents_success(self, mock_incidents, runner: CliRunner) -> None:
        mock_incidents.return_value = _ok({
            "incidents": [
                {
                    "id": 1,
                    "agent_id": "mani-ruf-01",
                    "incident_type": "data_breach",
                    "description": "Unauthorized access detected",
                    "severity": "high",
                    "status": "detected",
                    "detected_at": "2026-03-25T10:00:00Z",
                    "report_deadline": "2026-03-28T10:00:00Z",
                },
            ],
            "total": 1,
        })
        result = runner.invoke(main, ["incidents"])
        assert result.exit_code == 0
        # Rich may truncate column values — check for prefix
        assert "mani-ruf" in result.output
        assert "data_brea" in result.output

    @patch("nomos.core.api.get_incidents")
    def test_incidents_empty(self, mock_incidents, runner: CliRunner) -> None:
        mock_incidents.return_value = _ok({"incidents": [], "total": 0})
        result = runner.invoke(main, ["incidents"])
        assert result.exit_code == 0
        assert "Keine Incidents" in result.output

    @patch("nomos.core.api.get_incidents")
    def test_incidents_error(self, mock_incidents, runner: CliRunner) -> None:
        mock_incidents.return_value = _err("Interner Serverfehler")
        result = runner.invoke(main, ["incidents"])
        assert result.exit_code != 0


# ═══════════════════════════════════════════════════════════════════════════
# 9. workspace mount
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceMount:
    @patch("nomos.core.api.mount_collection")
    def test_mount_success(self, mock_mount, runner: CliRunner) -> None:
        mock_mount.return_value = _ok({
            "agent_id": "mani-ruf-01",
            "collection_name": "brand-guidelines",
            "mounted": True,
        })
        result = runner.invoke(main, ["workspace", "mount", "--agent", "mani-ruf-01", "--collection", "brand-guidelines"])
        assert result.exit_code == 0
        assert "gemountet" in result.output
        assert "brand-guidelines" in result.output

    @patch("nomos.core.api.mount_collection")
    def test_mount_error(self, mock_mount, runner: CliRunner) -> None:
        mock_mount.return_value = _err("Cannot mount collection for agent mani-ruf-01", 400)
        result = runner.invoke(main, ["workspace", "mount", "--agent", "mani-ruf-01", "--collection", "invalid"])
        assert result.exit_code != 0
        assert "Fehler" in result.output


# ═══════════════════════════════════════════════════════════════════════════
# 10. workspace unmount
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceUnmount:
    @patch("nomos.core.api.unmount_collection")
    def test_unmount_success(self, mock_unmount, runner: CliRunner) -> None:
        mock_unmount.return_value = _ok({
            "agent_id": "mani-ruf-01",
            "collection_name": "brand-guidelines",
            "mounted": False,
        })
        result = runner.invoke(main, ["workspace", "unmount", "--agent", "mani-ruf-01", "--collection", "brand-guidelines"])
        assert result.exit_code == 0
        assert "ausgehaengt" in result.output
        assert "brand-guidelines" in result.output

    @patch("nomos.core.api.unmount_collection")
    def test_unmount_not_found(self, mock_unmount, runner: CliRunner) -> None:
        mock_unmount.return_value = _err("Collection brand-guidelines not mounted", 404)
        result = runner.invoke(main, ["workspace", "unmount", "--agent", "mani-ruf-01", "--collection", "brand-guidelines"])
        assert result.exit_code != 0
        assert "Fehler" in result.output


# ═══════════════════════════════════════════════════════════════════════════
# API client unit tests
# ═══════════════════════════════════════════════════════════════════════════


class TestApiClient:
    """Tests for the API client module itself (retry, error handling)."""

    def test_connection_error(self, monkeypatch) -> None:
        """Connection refused produces a human-readable error."""
        monkeypatch.setattr(api, "RETRY_DELAY", 0)
        monkeypatch.setattr(api, "_base_url", lambda: "http://localhost:9999")
        result = api.pause_agent("test-agent")
        assert result["success"] is False
        assert "Verbindung" in result["error"] or "fehlgeschlagen" in result["error"]

    def test_ok_helper(self) -> None:
        from nomos.core.api import _ok
        r = _ok({"x": 1})
        assert r == {"success": True, "data": {"x": 1}}

    def test_err_helper(self) -> None:
        from nomos.core.api import _err
        r = _err("boom", 500)
        assert r == {"success": False, "error": "boom", "status_code": 500}


# Import api at module level so TestApiClient can reference it
from nomos.core import api
