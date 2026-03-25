"""Tests for NomOS Event Types v2 — incident, PII, kill switch, and data events."""

from __future__ import annotations

from nomos.core.events import EventType, validate_event_type


class TestIncidentEvents:
    def test_incident_detected(self) -> None:
        assert EventType.INCIDENT_DETECTED == "incident.detected"
        assert validate_event_type("incident.detected") is True

    def test_incident_reported(self) -> None:
        assert EventType.INCIDENT_REPORTED == "incident.reported"
        assert validate_event_type("incident.reported") is True

    def test_incident_resolved(self) -> None:
        assert EventType.INCIDENT_RESOLVED == "incident.resolved"
        assert validate_event_type("incident.resolved") is True


class TestPIIEvents:
    def test_pii_filtered(self) -> None:
        assert EventType.PII_FILTERED == "pii.filtered"
        assert validate_event_type("pii.filtered") is True

    def test_pii_leak_detected(self) -> None:
        assert EventType.PII_LEAK_DETECTED == "pii.leak_detected"
        assert validate_event_type("pii.leak_detected") is True


class TestKillSwitchEvents:
    def test_kill_switch_activated(self) -> None:
        assert EventType.KILL_SWITCH_ACTIVATED == "kill_switch.activated"
        assert validate_event_type("kill_switch.activated") is True

    def test_kill_switch_user_pause(self) -> None:
        assert EventType.KILL_SWITCH_USER_PAUSE == "kill_switch.user_pause"
        assert validate_event_type("kill_switch.user_pause") is True


class TestDataEvents:
    def test_data_retention_enforced(self) -> None:
        assert EventType.DATA_RETENTION_ENFORCED == "data.retention_enforced"
        assert validate_event_type("data.retention_enforced") is True

    def test_data_erased(self) -> None:
        assert EventType.DATA_ERASED == "data.erased"
        assert validate_event_type("data.erased") is True


class TestExistingEventsStillWork:
    def test_agent_created_still_valid(self) -> None:
        assert validate_event_type("agent.created") is True

    def test_governance_kill_switch_still_valid(self) -> None:
        assert validate_event_type("governance.kill_switch") is True
