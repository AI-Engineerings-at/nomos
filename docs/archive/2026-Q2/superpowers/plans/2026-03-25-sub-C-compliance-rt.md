# Sub-Projekt C: Compliance Runtime — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PII Filter Runtime Engine (Python-seitig mit NER), Kill Switch Enforcement, Compliance Gate v2 (5→14 Dokumente), Incident Detection + Response (Art. 33/34 DSGVO).

**Architecture:** Erweitert die bestehende Core Library (nomos-cli) und API (nomos-api). PII Filter ist die Python-Engine die vom Plugin (TypeScript, sync Regex) aufgerufen wird — die Python-Version hat die volle NER-Pipeline. Gate v2 erweitert gate.py um 9 neue Dokumente.

**Tech Stack:** Python 3.12, spaCy (NER), Pydantic v2, FastAPI, pytest

**Design Spec:** `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` Sektionen 4, 9, 10
**Master Plan:** `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md` Sub-Projekt C

---

## File Structure

```
Neue Dateien:
  nomos-cli/nomos/core/pii_filter.py             # PII Runtime: Regex + Pattern + optional NER
  nomos-cli/nomos/core/incident.py                # Incident Detection + 72h Timer
  nomos-api/nomos_api/services/pii.py             # PII API Service
  nomos-api/nomos_api/services/incident.py        # Incident API Service
  nomos-api/nomos_api/routers/incidents.py         # REST /api/incidents/*
  nomos-api/nomos_api/routers/pii.py              # REST /api/pii/*

Erweitern:
  nomos-cli/nomos/core/gate.py                    # +9 neue Dokumente (6-14)
  nomos-cli/nomos/core/events.py                  # +incident.*, +pii.*, +kill_switch.*
  nomos-api/nomos_api/models.py                   # +Incident Model
  nomos-api/nomos_api/schemas.py                  # +PII/Incident Schemas
  nomos-api/nomos_api/main.py                     # +neue Router

Tests:
  nomos-cli/tests/test_pii_filter.py
  nomos-cli/tests/test_incident.py
  nomos-cli/tests/test_gate_v2.py
  nomos-api/tests/test_pii_api.py
  nomos-api/tests/test_incidents_api.py
```

---

## Task 1: PII Filter Engine (Core Library)

**Files:**
- Create: `nomos-cli/nomos/core/pii_filter.py`
- Test: `nomos-cli/tests/test_pii_filter.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-cli/tests/test_pii_filter.py
from nomos.core.pii_filter import PIIFilter, PIIMatch

def test_detect_email():
    f = PIIFilter()
    result = f.filter("Kontakt: max@example.com bitte")
    assert "[EMAIL_REDACTED]" in result.filtered_text
    assert any(m.pii_type == "email" for m in result.matches)

def test_detect_phone_austrian():
    f = PIIFilter()
    result = f.filter("Ruf an: +43 1 234 5678")
    assert "[PHONE_REDACTED]" in result.filtered_text

def test_detect_iban():
    f = PIIFilter()
    result = f.filter("IBAN: AT611904300234573201")
    assert "[IBAN_REDACTED]" in result.filtered_text

def test_detect_multiple_pii():
    f = PIIFilter()
    result = f.filter("max@test.com anrufen unter +43 664 1234567")
    assert result.pii_count == 2
    assert "[EMAIL_REDACTED]" in result.filtered_text
    assert "[PHONE_REDACTED]" in result.filtered_text

def test_no_pii():
    f = PIIFilter()
    result = f.filter("Keine persoenlichen Daten hier.")
    assert result.pii_count == 0
    assert result.filtered_text == "Keine persoenlichen Daten hier."

def test_german_address_pattern():
    f = PIIFilter()
    result = f.filter("Wohnt in Musterstrasse 42, 1010 Wien")
    assert "[ADDRESS_REDACTED]" in result.filtered_text

def test_preserves_non_pii_content():
    f = PIIFilter()
    text = "Projekt NomOS v2 hat 105 Tests. Email: test@firma.at"
    result = f.filter(text)
    assert "Projekt NomOS v2 hat 105 Tests" in result.filtered_text
    assert "test@firma.at" not in result.filtered_text
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Implement pii_filter.py**

```python
# nomos-cli/nomos/core/pii_filter.py
from dataclasses import dataclass, field
import re

@dataclass
class PIIMatch:
    pii_type: str
    original: str
    start: int
    end: int

@dataclass
class PIIFilterResult:
    filtered_text: str
    matches: list[PIIMatch] = field(default_factory=list)

    @property
    def pii_count(self) -> int:
        return len(self.matches)

_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}"), "[EMAIL_REDACTED]"),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7,}[A-Z0-9]{0,16}\b"), "[IBAN_REDACTED]"),
    ("phone", re.compile(r"\+\d{1,3}\s?\d{1,4}[\s.-]?\d{2,4}[\s.-]?\d{2,8}"), "[PHONE_REDACTED]"),
    ("address", re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]+(?:strasse|gasse|weg|platz)\s+\d+[a-z]?,\s*\d{4,5}\s+[A-ZÄÖÜ][a-zäöüß]+\b"), "[ADDRESS_REDACTED]"),
    ("tax_id", re.compile(r"\b\d{2,3}/\d{3,4}/\d{4,5}\b"), "[TAX_ID_REDACTED]"),
]

class PIIFilter:
    def __init__(self, use_ner: bool = False):
        self._use_ner = use_ner

    def filter(self, text: str) -> PIIFilterResult:
        matches: list[PIIMatch] = []
        result = text

        for pii_type, pattern, replacement in _PATTERNS:
            for match in pattern.finditer(result):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    original=match.group(),
                    start=match.start(),
                    end=match.end(),
                ))
            result = pattern.sub(replacement, result)

        return PIIFilterResult(filtered_text=result, matches=matches)
```

Note: NER (spaCy) is optional enhancement — Regex-basiert ist der Startpunkt. NER wird bei high-risk Agents zugeschaltet (spaetere Erweiterung, kein Placeholder).

- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 2: Compliance Gate v2 (5→14 Dokumente)

**Files:**
- Modify: `nomos-cli/nomos/core/gate.py`
- Test: `nomos-cli/tests/test_gate_v2.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-cli/tests/test_gate_v2.py
from pathlib import Path
from nomos.core.gate import generate_compliance_docs, REQUIRED_DOCS_V2

def test_v2_generates_14_docs(tmp_path: Path):
    manifest_data = _valid_high_risk_manifest()
    docs = generate_compliance_docs(manifest_data, tmp_path)
    assert len(docs) == 14

def test_v2_doc_names():
    assert len(REQUIRED_DOCS_V2) == 14
    assert "dpia" in REQUIRED_DOCS_V2
    assert "avv" in REQUIRED_DOCS_V2
    assert "risk_management" in REQUIRED_DOCS_V2
    assert "tia" in REQUIRED_DOCS_V2
    assert "incident_response" in REQUIRED_DOCS_V2
    assert "tom" in REQUIRED_DOCS_V2
    assert "accessibility" in REQUIRED_DOCS_V2

def test_limited_risk_gets_9_docs(tmp_path: Path):
    manifest_data = _valid_limited_risk_manifest()
    docs = generate_compliance_docs(manifest_data, tmp_path)
    assert len(docs) == 9  # limited risk needs fewer docs

def test_us_location_generates_tia(tmp_path: Path):
    manifest_data = _valid_manifest_us_location()
    docs = generate_compliance_docs(manifest_data, tmp_path)
    doc_names = [d["name"] for d in docs]
    assert "tia" in doc_names

def test_each_doc_has_content(tmp_path: Path):
    manifest_data = _valid_high_risk_manifest()
    docs = generate_compliance_docs(manifest_data, tmp_path)
    for doc in docs:
        assert len(doc["content"]) > 100, f"Doc {doc['name']} is too short"

def test_docs_contain_disclaimer(tmp_path: Path):
    manifest_data = _valid_high_risk_manifest()
    docs = generate_compliance_docs(manifest_data, tmp_path)
    for doc in docs:
        assert "NomOS" in doc["content"]
        assert "ersetzt keine" in doc["content"] or "does not replace" in doc["content"]
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Extend gate.py**

Add 9 new document generators:
```
6.  AVV (Auftragsverarbeitungsvertrag) — Art. 28 DSGVO
7.  Risk Management Report — Art. 9 EU AI Act
8.  Betroffenenrechte-Prozess — Art. 15, 17 DSGVO
9.  AI Literacy Checklist — Art. 4 EU AI Act
10. Transfer Impact Assessment (TIA) — Schrems II (nur bei US-Location)
11. Art. 22 Policy — Automatisierte Entscheidungen
12. Incident Response Plan — Art. 33/34 DSGVO
13. TOM-Dokumentation — Art. 32 DSGVO
14. Barrierefreiheitserklaerung — BFSG
```

Every doc includes disclaimer: "Automatisch generiert von NomOS. Dieses Dokument ersetzt keine individuelle Rechtsberatung."

- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 3: Incident Detection + 72h Timer

**Files:**
- Create: `nomos-cli/nomos/core/incident.py`
- Test: `nomos-cli/tests/test_incident.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-cli/tests/test_incident.py
from nomos.core.incident import detect_incident, IncidentType, Incident
from datetime import datetime, timezone, timedelta

def test_detect_pii_in_log():
    incident = detect_incident("Log entry: user max@example.com logged in")
    assert incident is not None
    assert incident.incident_type == IncidentType.PII_IN_LOG

def test_detect_unknown_endpoint():
    incident = detect_incident(
        "Agent sent data to https://evil.com/collect",
        context={"allowed_endpoints": ["https://api.anthropic.com"]}
    )
    assert incident is not None
    assert incident.incident_type == IncidentType.UNKNOWN_ENDPOINT

def test_no_incident_for_clean_log():
    incident = detect_incident("Normal operation completed successfully")
    assert incident is None

def test_incident_has_72h_deadline():
    incident = detect_incident("PII leak: max@test.com in plaintext")
    assert incident is not None
    expected = incident.detected_at + timedelta(hours=72)
    assert incident.report_deadline == expected

def test_incident_severity():
    incident = detect_incident("max@test.com in log")
    assert incident.severity in ("critical", "high", "medium", "low")
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Implement incident.py**

```python
# nomos-cli/nomos/core/incident.py
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
import re

class IncidentType(Enum):
    PII_IN_LOG = "pii_in_log"
    UNKNOWN_ENDPOINT = "unknown_endpoint"
    HASH_TAMPER = "hash_tamper"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

@dataclass
class Incident:
    incident_type: IncidentType
    description: str
    severity: str
    detected_at: datetime
    report_deadline: datetime  # 72h DSGVO Art. 33

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}")
_URL_PATTERN = re.compile(r"https?://[\w.-]+(?:/[\w./-]*)?")

def detect_incident(
    log_entry: str,
    context: dict | None = None,
) -> Incident | None:
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=72)

    # PII in plaintext log
    if _EMAIL_PATTERN.search(log_entry):
        return Incident(
            incident_type=IncidentType.PII_IN_LOG,
            description=f"PII (email) detected in log entry",
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
```

- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 4: Extend Events (incident, pii, kill_switch)

**Files:**
- Modify: `nomos-cli/nomos/core/events.py`
- Test: `nomos-cli/tests/test_events_v2.py` (extend from Sub-B)

- [ ] **Step 1: Add new event types**

```python
# Add to EventType enum:
INCIDENT_DETECTED = "incident.detected"
INCIDENT_REPORTED = "incident.reported"
INCIDENT_RESOLVED = "incident.resolved"
PII_FILTERED = "pii.filtered"
PII_LEAK_DETECTED = "pii.leak_detected"
KILL_SWITCH_ACTIVATED = "kill_switch.activated"
KILL_SWITCH_USER_PAUSE = "kill_switch.user_pause"
DATA_RETENTION_ENFORCED = "data.retention_enforced"
DATA_ERASED = "data.erased"
```

- [ ] **Step 2: Test + commit**

---

## Task 5: PII API Service + Router

**Files:**
- Create: `nomos-api/nomos_api/services/pii.py`
- Create: `nomos-api/nomos_api/routers/pii.py`
- Test: `nomos-api/tests/test_pii_api.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_pii_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from nomos_api.main import app

@pytest.mark.anyio
async def test_filter_pii():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/pii/filter", json={
            "text": "Email: max@example.com, Tel: +43 1 234 5678"
        })
        assert response.status_code == 200
        data = response.json()
        assert "[EMAIL_REDACTED]" in data["filtered"]
        assert data["pii_count"] >= 1

@pytest.mark.anyio
async def test_filter_clean_text():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/pii/filter", json={
            "text": "Keine PII hier"
        })
        data = response.json()
        assert data["pii_count"] == 0
        assert data["filtered"] == "Keine PII hier"
```

- [ ] **Step 2-5: Implement + test + commit**

---

## Task 6: Incident API Service + Router

**Files:**
- Create: `nomos-api/nomos_api/services/incident.py`
- Create: `nomos-api/nomos_api/routers/incidents.py`
- Modify: `nomos-api/nomos_api/models.py` (+Incident model)
- Test: `nomos-api/tests/test_incidents_api.py`

Endpoints:
```
POST  /api/incidents              → create incident
GET   /api/incidents              → list incidents
PATCH /api/incidents/{id}         → update status (reported, resolved)
```

- [ ] **Step 1-5: Implement with TDD**

---

## Task 7: Kill Switch (in agents router)

**Files:**
- Modify: `nomos-api/nomos_api/routers/agents.py`

The kill switch is implemented as part of the PATCH /api/agents/{id} endpoint (already planned in Sub-B). In Sub-C we add:
- POST /api/agents/{id}/kill → permanent stop (admin only)
- Audit entry: "kill_switch.activated"
- Verification: Agent status changes to "killed" within 5 seconds

- [ ] **Step 1: Write test for kill switch response time**
- [ ] **Step 2: Implement**
- [ ] **Step 3: Commit**

---

## Task 8: Register Routes + Integration Test

- [ ] **Step 1: Register pii + incidents routers in main.py**
- [ ] **Step 2: Run ALL tests**

```bash
cd nomos-cli && python -m pytest tests/ -v
cd nomos-api && python -m pytest tests/ -v
```

Expected: All pass, 0 regressions

- [ ] **Step 3: Commit**

---

## Erfolgs-Kriterien

- [ ] PII Filter: Email, Telefon, IBAN, Adresse, Steuernummer erkannt + maskiert
- [ ] 14 Compliance-Dokumente generiert (high-risk)
- [ ] 9 Dokumente fuer limited-risk
- [ ] TIA nur bei US-Location generiert
- [ ] Jedes Dokument hat Disclaimer
- [ ] Incident Detection: PII in Log, unbekannter Endpoint
- [ ] 72h Timer bei jedem Incident
- [ ] Kill Switch: Agent-Status → "killed"
- [ ] Neue Event Types registriert
- [ ] PII API Endpoint funktioniert
- [ ] Incident API Endpoint funktioniert
- [ ] Alle Tests gruen, 0 Regressions
