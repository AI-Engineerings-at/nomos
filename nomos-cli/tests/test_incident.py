"""Tests for NomOS Incident Detection — Art. 33/34 DSGVO compliance."""

from __future__ import annotations

from datetime import timedelta

from nomos.core.incident import detect_incident, IncidentType, Incident


class TestPIIInLogDetection:
    def test_detect_pii_in_log(self) -> None:
        incident = detect_incident("Log entry: user max@example.com logged in")
        assert incident is not None
        assert incident.incident_type == IncidentType.PII_IN_LOG

    def test_pii_incident_severity_is_high(self) -> None:
        incident = detect_incident("max@test.com in log")
        assert incident is not None
        assert incident.severity == "high"


class TestUnknownEndpointDetection:
    def test_detect_unknown_endpoint(self) -> None:
        incident = detect_incident(
            "Agent sent data to https://evil.com/collect",
            context={"allowed_endpoints": ["https://api.anthropic.com"]},
        )
        assert incident is not None
        assert incident.incident_type == IncidentType.UNKNOWN_ENDPOINT

    def test_allowed_endpoint_no_incident(self) -> None:
        incident = detect_incident(
            "Agent sent data to https://api.anthropic.com/v1/messages",
            context={"allowed_endpoints": ["https://api.anthropic.com"]},
        )
        assert incident is None

    def test_unknown_endpoint_severity_is_critical(self) -> None:
        incident = detect_incident(
            "Agent sent data to https://evil.com/collect",
            context={"allowed_endpoints": ["https://api.anthropic.com"]},
        )
        assert incident is not None
        assert incident.severity == "critical"


class TestCleanLogs:
    def test_no_incident_for_clean_log(self) -> None:
        incident = detect_incident("Normal operation completed successfully")
        assert incident is None

    def test_no_incident_without_context(self) -> None:
        incident = detect_incident("Accessing https://api.anthropic.com/v1/messages")
        assert incident is None


class TestIncident72hDeadline:
    def test_incident_has_72h_deadline(self) -> None:
        incident = detect_incident("PII leak: max@test.com in plaintext")
        assert incident is not None
        expected = incident.detected_at + timedelta(hours=72)
        assert incident.report_deadline == expected


class TestIncidentSeverity:
    def test_incident_severity_valid(self) -> None:
        incident = detect_incident("max@test.com in log")
        assert incident is not None
        assert incident.severity in ("critical", "high", "medium", "low")


class TestIncidentType:
    def test_all_types_defined(self) -> None:
        assert IncidentType.PII_IN_LOG.value == "pii_in_log"
        assert IncidentType.UNKNOWN_ENDPOINT.value == "unknown_endpoint"
        assert IncidentType.HASH_TAMPER.value == "hash_tamper"
        assert IncidentType.UNAUTHORIZED_ACCESS.value == "unauthorized_access"
