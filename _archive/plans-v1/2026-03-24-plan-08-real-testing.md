# Plan 8: Real Testing — Von 0 bis 100% wie ein User

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jeder Button geklickt, jeder CLI-Befehl ausgefuehrt, Audit Trail downloadbar, OpenClaw Plugin geladen, alles dokumentiert mit Beweis.

**Architecture:** Fehlende Features bauen (Audit Export Endpoint, Download Button in UI), dann ALLES testen — UI, CLI, API, Plugin, Mattermost. Jeder Test mit Beweis (HTTP Response, Console Output, Log).

**Tech Stack:** Python, TypeScript, Docker, curl, Playwright (optional), OpenClaw Gateway

---

## Was FEHLT (Features bauen BEVOR testen)

### Feature 1: Audit Trail Export Endpoint
API hat GET /api/agents/{id}/audit (JSON) aber KEINEN Download als Datei.
Braucht: GET /api/agents/{id}/audit/export → JSONL Datei Download

### Feature 2: Audit Download Button in Console
Console zeigt Audit Trail als Tabelle aber hat KEINEN Download Button.
Braucht: "Audit Trail herunterladen" Button auf /agent/[id]

### Feature 3: Vollstaendiger Crypto Log
Jede Aktion (create, gate, verify) muss im Hash Chain protokolliert werden.
Aktuell: Nur agent.created Event. Gate + Verify Events fehlen.

---

## Task 1: Audit Export API Endpoint

**Files:**
- Modify: `nomos-api/nomos_api/routers/audit.py`
- Modify: `nomos-api/tests/test_audit.py`

- [ ] **Step 1: Add export endpoint to audit.py**

```python
from fastapi.responses import PlainTextResponse

@router.get("/agents/{agent_id}/audit/export")
async def export_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export audit trail as downloadable JSONL file."""
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")

    chain_file = agent_dir / "audit" / "chain.jsonl"
    if not chain_file.exists():
        return PlainTextResponse("", media_type="application/jsonl")

    content = chain_file.read_text(encoding="utf-8")
    return PlainTextResponse(
        content,
        media_type="application/jsonl",
        headers={
            "Content-Disposition": f'attachment; filename="{agent_id}-audit-chain.jsonl"'
        },
    )
```

- [ ] **Step 2: Add test**

```python
class TestAuditExport:
    async def test_export_returns_jsonl(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Export Test", "role": "test", "company": "Co", "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        resp = await client.get(f"/api/agents/{agent_id}/audit/export")
        assert resp.status_code == 200
        assert "agent.created" in resp.text
        assert resp.headers.get("content-disposition", "").endswith('.jsonl"')
```

- [ ] **Step 3: Run tests, commit**

---

## Task 2: Gate + Verify Events im Hash Chain

**Files:**
- Modify: `nomos-api/nomos_api/routers/compliance.py` (gate endpoint)
- Modify: `nomos-cli/nomos/core/hash_chain.py` (braucht evtl. keine Aenderung)

- [ ] **Step 1: Gate endpoint schreibt Event in Hash Chain**

Wenn POST /api/agents/{id}/gate aufgerufen wird, NACH dem Generieren der Docs:

```python
# In run_compliance_gate(), after generate_compliance_docs:
from nomos.core.hash_chain import HashChain
from nomos.core.events import EventType

chain = HashChain(storage_dir=agent_dir / "audit")
chain.append(
    event_type=EventType.COMPLIANCE_CHECK_PASSED if result.status.value == "passed" else EventType.COMPLIANCE_CHECK_FAILED,
    agent_id=agent_id,
    data={
        "status": result.status.value,
        "documents_generated": len(manifest.compliance.documents_required),
        "missing": result.missing_documents,
    },
)

# Also index in DB
from nomos_api.models import AuditLog
for entry in chain.entries[-1:]:  # Only the new entry
    audit_log = AuditLog(
        agent_id=entry.agent_id,
        sequence=entry.sequence,
        event_type=entry.event_type,
        data=entry.data,
        chain_hash=entry.hash,
        timestamp=entry.timestamp,
    )
    db.add(audit_log)
```

- [ ] **Step 2: Test that gate creates audit entry**

```python
async def test_gate_creates_audit_entry(self, client) -> None:
    create_resp = await client.post("/api/agents", json={...})
    agent_id = create_resp.json()["id"]
    await client.post(f"/api/agents/{agent_id}/gate")
    audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
    entries = audit_resp.json()["entries"]
    assert len(entries) >= 2  # agent.created + compliance.check.passed
    assert entries[-1]["event_type"] == "compliance.check.passed"
```

- [ ] **Step 3: Run tests, commit**

---

## Task 3: Download Button in Console

**Files:**
- Modify: `nomos-console/src/app/agent/[id]/page.tsx`

- [ ] **Step 1: Add download link to audit trail section**

```tsx
<a
  href={`${API_URL}/api/agents/${id}/audit/export`}
  download={`${id}-audit-chain.jsonl`}
  className="text-sm text-blue-600 hover:underline"
>
  Audit Trail herunterladen (JSONL)
</a>
```

- [ ] **Step 2: Build console**
- [ ] **Step 3: Commit**

---

## Task 4: REAL UI Test — Jeden Button klicken

**Voraussetzung:** Docker Stack laeuft (API + Console)

- [ ] **Test 4.1: Homepage laden**
Browser: http://localhost:3045/
Erwartung: Fleet Tabelle, "Mitarbeiter einstellen" Button sichtbar
Beweis: curl + HTML grep

- [ ] **Test 4.2: "Mitarbeiter einstellen" klicken → Formular**
Browser: http://localhost:3045/fleet
Erwartung: Form mit Name, Rolle, Firma, Email, Risiko, Submit Button
Beweis: curl + HTML grep fuer form elements

- [ ] **Test 4.3: Formular ausfuellen + Submit**
POST /api/agents mit echten Daten
Erwartung: Agent erstellt, Redirect zu /agent/{id}
Beweis: API Response + Agent Detail Page laed

- [ ] **Test 4.4: Agent Detail → Compliance BLOCKED sehen**
Browser: http://localhost:3045/agent/{id}
Erwartung: "Compliance: BLOCKED", "Compliance-Dokumente generieren" Button
Beweis: curl + HTML grep

- [ ] **Test 4.5: "Compliance-Dokumente generieren" klicken**
POST /api/agents/{id}/gate
Erwartung: 5 Docs generiert, Status PASSED
Beweis: API Response

- [ ] **Test 4.6: Agent Detail → Compliance PASSED sehen**
Browser refresh
Erwartung: "Compliance: PASSED", Audit Trail mit 2 Eintraegen
Beweis: curl + HTML grep

- [ ] **Test 4.7: Audit Trail sehen**
Erwartung: agent.created + compliance.check.passed Events
Beweis: API /audit Response

- [ ] **Test 4.8: "Audit Trail herunterladen" klicken**
GET /api/agents/{id}/audit/export
Erwartung: JSONL Datei download
Beweis: Content-Disposition Header + Dateiinhalt

- [ ] **Test 4.9: Chain kryptographisch verifizieren**
GET /api/audit/verify/{id}
Erwartung: valid=true, entries_checked>=2
Beweis: API Response

- [ ] **Test 4.10: Fleet zeigt Agent mit passed**
Browser: http://localhost:3045/
Erwartung: 1 Agent in Tabelle, Compliance: passed
Beweis: curl + HTML grep

---

## Task 5: REAL CLI Test — Terminal Workflow

- [ ] **Test 5.1: nomos --version**
- [ ] **Test 5.2: nomos hire (neuer Agent)**
- [ ] **Test 5.3: nomos gate (Docs generieren)**
- [ ] **Test 5.4: nomos verify (4/4 PASS)**
- [ ] **Test 5.5: nomos fleet (1 Agent, passed)**
- [ ] **Test 5.6: nomos audit (2+ Events)**
- [ ] **Test 5.7: nomos audit --verify (chain VALID)**

Jeder Test mit vollstaendigem Output als Beweis.

---

## Task 6: Dokumentation der Testergebnisse

- [ ] Alle Ergebnisse in ERPNext Note speichern
- [ ] Alle Ergebnisse in open-notebook Source speichern
- [ ] Git commit mit Test-Dokumentation

---

## Was NICHT in diesem Plan ist (kommt spaeter)

- OpenClaw Plugin in echtem Gateway laden (braucht Gateway-Start)
- Mattermost Test (braucht Mani + Gateway)
- Playwright automatisierte Browser-Tests (Enhancement)
- Performance Tests
- Security Penetration Test
