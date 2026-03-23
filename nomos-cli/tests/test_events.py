"""Tests for NomOS Event Types."""

from __future__ import annotations

from nomos.core.events import (
    EventType,
    NomOSEvent,
    validate_event_type,
)


class TestEventType:
    def test_all_lifecycle_events_exist(self) -> None:
        assert EventType.AGENT_CREATED == "agent.created"
        assert EventType.AGENT_DEPLOYED == "agent.deployed"
        assert EventType.AGENT_STOPPED == "agent.stopped"
        assert EventType.AGENT_RETIRED == "agent.retired"

    def test_all_compliance_events_exist(self) -> None:
        assert EventType.COMPLIANCE_CHECK_PASSED == "compliance.check.passed"
        assert EventType.COMPLIANCE_CHECK_FAILED == "compliance.check.failed"
        assert EventType.COMPLIANCE_DOC_SIGNED == "compliance.doc.signed"

    def test_all_governance_events_exist(self) -> None:
        assert EventType.GOVERNANCE_HOOK_TRIGGERED == "governance.hook.triggered"
        assert EventType.GOVERNANCE_HOOK_BLOCKED == "governance.hook.blocked"
        assert EventType.GOVERNANCE_KILL_SWITCH == "governance.kill_switch"
        assert EventType.GOVERNANCE_ESCALATION == "governance.escalation"

    def test_all_audit_events_exist(self) -> None:
        assert EventType.AUDIT_CHAIN_CREATED == "audit.chain.created"
        assert EventType.AUDIT_CHAIN_VERIFIED == "audit.chain.verified"
        assert EventType.AUDIT_EXPORTED == "audit.exported"


class TestNomOSEvent:
    def test_event_creation(self) -> None:
        event = NomOSEvent(
            event_type=EventType.AGENT_CREATED,
            agent_id="mani-v1",
            data={"name": "Mani Ruf"},
        )
        assert event.event_type == "agent.created"
        assert event.agent_id == "mani-v1"
        assert event.data == {"name": "Mani Ruf"}
        assert event.timestamp

    def test_event_to_dict(self) -> None:
        event = NomOSEvent(
            event_type=EventType.AGENT_CREATED,
            agent_id="mani-v1",
            data={},
        )
        d = event.to_dict()
        assert "event_type" in d
        assert "agent_id" in d
        assert "timestamp" in d
        assert "data" in d


class TestValidateEventType:
    def test_valid_event_type(self) -> None:
        assert validate_event_type("agent.created") is True

    def test_invalid_event_type(self) -> None:
        assert validate_event_type("invalid.event") is False

    def test_custom_prefix_valid(self) -> None:
        assert validate_event_type("agent.custom_action") is False
