"""NomOS Incident Detection — Art. 33/34 DSGVO compliance.

Detects security and privacy incidents in agent logs and enforces the
72-hour reporting deadline required by Art. 33 DSGVO. Incidents are
classified by type and severity for appropriate response handling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum


class IncidentType(Enum):
    """Types of detectable incidents."""

    PII_IN_LOG = "pii_in_log"
    UNKNOWN_ENDPOINT = "unknown_endpoint"
    HASH_TAMPER = "hash_tamper"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class Incident:
    """A detected security or privacy incident."""

    incident_type: IncidentType
    description: str
    severity: str  # "critical", "high", "medium", "low"
    detected_at: datetime
    report_deadline: datetime  # 72h DSGVO Art. 33


_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}")
_URL_PATTERN = re.compile(r"https?://[\w.-]+(?:/[\w./-]*)?")


def detect_incident(
    log_entry: str,
    context: dict | None = None,
) -> Incident | None:
    """Analyze a log entry for potential incidents.

    Checks for PII in plaintext logs and unauthorized endpoint access.
    Returns an Incident with 72h reporting deadline if found, None otherwise.

    Args:
        log_entry: The log text to analyze.
        context: Optional dict with 'allowed_endpoints' list for endpoint checks.
    """
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=72)

    # PII in plaintext log
    if _EMAIL_PATTERN.search(log_entry):
        return Incident(
            incident_type=IncidentType.PII_IN_LOG,
            description="PII (email) detected in log entry",
            severity="high",
            detected_at=now,
            report_deadline=deadline,
        )

    # Unknown endpoint
    if context and "allowed_endpoints" in context:
        urls = _URL_PATTERN.findall(log_entry)
        allowed = context["allowed_endpoints"]
        for url in urls:
            if not any(url.startswith(a) for a in allowed):
                return Incident(
                    incident_type=IncidentType.UNKNOWN_ENDPOINT,
                    description=f"Data sent to unauthorized endpoint: {url}",
                    severity="critical",
                    detected_at=now,
                    report_deadline=deadline,
                )

    return None
