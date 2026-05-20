# NomOS ↔ Atlas Integration Spec (v0.7.0+)

> Konkrete Contracts wie Atlas (Joe's HQ-Operator-Cockpit) und NomOS
> (Customer-Compliance-Produkt) gekoppelt werden — die heute fehlende
> Brücke, die Phase 7 der NomOS-Roadmap definiert.
>
> Begleitdokument zu `2026-05-20-big-picture.md`.

---

## 1. Heute-Stand (2026-05-20)

**Es gibt KEINEN Code-Pfad zwischen Atlas und NomOS.**

| Concern | Atlas | NomOS |
|---|---|---|
| Audit-Trail | pino-redacted + audit_log SQLite | Hash-Chain JSONL + Ed25519 + RFC 6962 Merkle |
| Memory | sqlite-vec + Transformers.js (384d) | Postgres + pgvector + ContextPipeline |
| LLM-Router | `/v1/chat/completions` proxy mit Cost-Tracking | OpenClaw Gateway via Plugin oder Direct-LLM |
| Auth | Argon2id + AES-256-GCM Vault | JWT cookie + bcrypt + HashiCorp Vault |
| Deployment | Electron Desktop (Joe-host) | Docker Compose (Customer-host) |
| Database | SQLite (lokal) | Postgres 16 + pgvector |
| Network | Hard-coded `10.40.10.x` (internal lab) | configurierbar, no internal IPs |

Sie sind **disjunkt by design**: Atlas internal-only, NomOS
customer-shippable. Das ist kein Bug, sondern bewusste Trennung der
Concerns.

**Aber:** Atlas's MemoryEngine, audit_log und cost-tracking sind genau
die Artefakte die NomOS für **Annex-IV-Evidence** braucht. Atlas
fährt Joe's Agent-Fleet — Joe ist sein eigener Pilot-Customer. Wenn
Atlas-Events in NomOS-Audit-Trail landen, ist die Compliance-Geschichte
für Joe selbst geschlossen.

---

## 2. Future-Contract (v0.7.0)

### 2.1 Contract A: Atlas → NomOS Audit-Trail-Sink

Atlas's Agents emit Events. NomOS's Audit-Trail nimmt sie auf.

```
Atlas Agent A1 (running)
    │
    │  HookEngine fires:
    │    agent.tool.called
    │    agent.tool.completed
    │    agent.llm.requested
    │    agent.llm.responded (with cost)
    │    agent.memory.stored
    │    agent.approval.requested
    │    agent.approval.resolved
    │
    ▼
Atlas AuditSink (new component)
    │
    │  POST /api/audit/entry   (per event)
    │  X-NomOS-API-Key: <service-principal>
    │  body: {event_type, agent_id, data}
    │
    ▼
NomOS audit.append()
    │
    └─> Hash-Chain JSONL + Ed25519 sig
    └─> AuditLog DB row
    └─> available via STH/inclusion-proof
```

**Contract:**
- Atlas hat eine NomOS-Endpoint-URL + Service-API-Key in Vault
- Per-Hook ein non-blocking POST (Atlas darf NICHT auf NomOS-Response warten)
- Atlas's audit_log behält **alle** Events (Source-of-Truth lokal)
- NomOS bekommt eine **kompakte Untermenge** (event_type, agent_id,
  truncated payload) für externe Audit-Fähigkeit
- Bei NomOS-Down: Atlas puffert in lokaler Queue + retried (Atlas's
  vorhandene `automation_jobs` Tabelle erweitern)

**Schema-Mapping:**

| Atlas Event | NomOS EventType | Payload-Subset |
|---|---|---|
| `agent.created` | `AGENT_CREATED` | name, role, model |
| `agent.tool.called` | `TOOL_CALL_ALLOWED` oder `_BLOCKED` | tool_name, approval_id |
| `agent.tool.completed` | `TOOL_COMPLETED` | tool_name, duration_ms |
| `agent.llm.responded` | (neu) `LLM_REQUEST_COMPLETED` | provider, model, cost_eur, tokens_in/out |
| `agent.approval.resolved` | `GOVERNANCE_HOOK_TRIGGERED` | approval_id, resolved_by, decision |
| `agent.crashed` | `INCIDENT_DETECTED` | crash_kind, last_state |
| `agent.killed` | `KILL_SWITCH` | killer_id, reason |

NomOS-Side-Schema: **kein** Plugin-Required. Service-Principal Auth via
`X-NomOS-API-Key`. Schon implementiert in v0.2.1+.

### 2.2 Contract B: NomOS → Atlas Compliance-Verdict (synchron)

Joe will Atlas-Agents auch vor Ausführung gegen NomOS-Verdict prüfen.
Das ist Asimov-Gesetz-3-Pattern aus dem Zeroth-Stack.

```
Atlas Agent A1 (about to call tool T)
    │
    ▼
Atlas's ApprovalGate
    │
    │  GET /api/agents/{id}/compliance  (synchron, 200ms-budget)
    │  oder
    │  POST /api/compliance/gate {agent_id, intended_action, risk_class}
    │
    ▼
NomOS compliance_engine.check_compliance()
    │
    └─> verdict: passed | warning | blocked
    └─> reasons: ["missing doc: dpia.md", ...]
    └─> rule_ids: ["art-14", "art-12"]
    │
    ▼
Atlas decides: ABORT (blocked) | PROCEED-with-warning (warning) | PROCEED (passed)
```

**Contract:**
- Atlas blockt Tool-Execution wenn `verdict == "blocked"`
- Atlas zeigt Verdict + Reasons in Worker-Channel
- NomOS hat 200ms-Budget — bei Timeout: Atlas fällt zurück auf
  letzten cached verdict (fail-safe, not fail-open)
- Atlas cached verdict pro `(agent_id, action_type)` für 60s

---

## 3. Was muss in NomOS dafür neu sein

### 3.1 NomOS-Side (v0.7.0)

- [ ] **Service-Principal-only Audit-Entry-Batch**:
  `POST /api/audit/entries` (plural) statt einzeln — Atlas batched 20+ Events
- [ ] **Streaming-Endpoint** für Real-time: `WS /api/audit/stream/{agent_id}` (Atlas konsumiert auch eigene Events)
- [ ] **Cost-Tracking-Endpoint**: `POST /api/costs/llm-call` mit provider/model/tokens/cost_eur, hängt an existing budget-system
- [ ] **Risk-Class-Inheritance**: Atlas-Agent `manifest.risk_class` propagiert in verdict-API
- [ ] **EventType-Enum erweitern**: `LLM_REQUEST_COMPLETED`, `AGENT_CRASHED`, `AGENT_KILLED_BY_OPERATOR`
- [ ] **AuditEntry Atlas-Source-Marker**: jeder Atlas-Event-Eintrag carry `data.source: "atlas"` und `data.atlas_agent_id`
- [ ] **Rate-Limit**: separate Bucket für Atlas (höhere Limits als Customer)

### 3.2 Atlas-Side (v0.7.0)

- [ ] **NomOSAuditSink** in `src/main/services/`:
  - `enqueue(event)` non-blocking
  - drain-loop pro 5s
  - retry-with-backoff bei 5xx
  - dead-letter-queue als SQLite table
- [ ] **NomOSComplianceClient** in `src/main/services/`:
  - `check(agent_id, action) → Verdict`
  - 200ms timeout
  - LRU-Cache (60s TTL)
  - Settings für `nomos_url` + `nomos_api_key` (Vault-injected)
- [ ] **ApprovalGate-Erweiterung**:
  - bestehende user-confirm-flow bleibt
  - **vor** user-confirm: NomOS-verdict-check
  - bei `blocked`: gar nicht erst zum user
- [ ] **HookEngine-Integration**:
  - jedes registered-hook fires NomOS-event parallel
  - opt-in via Settings (Joe kann's für lokale Experimente abschalten)
- [ ] **Settings-UI**: `NomOS Backend` Card (URL, API-Key, Test-Connection-Button, Live-Status-Indicator)

---

## 4. Was Atlas heute bringt das NomOS noch nicht hat

| Atlas-Feature | Wert für NomOS |
|---|---|
| **Sentinel-Gate** (Phase 4.4) — pre-completion verification, max 3 retries | NomOS könnte dies als "compliance-verified" Tag im Audit-Eintrag annotieren |
| **Auto-Learner** (Phase 4.5) — failure→success patterns | Customer-Telemetry → Compliance-Rule-Verbesserung |
| **Procedural Memory** | Compliance-Lessons-Learned als nomos-native Skill-Quelle |
| **CEO/Worker-Channels** | Pattern für NomOS Console Real-time-Updates |
| **OpenAI-kompatibler LLM-Proxy** mit Cost-Tracking pro Agent | NomOS hat heute Direct-LLM oder Gateway — Atlas's Cost-Tracking ist sauberer |
| **3-Memory-Engine** (episodic/semantic/procedural) | NomOS ContextPipeline ist nur episodic |
| **Skill-Loader mit YAML-Frontmatter + Trigger** | NomOS hat kein Skill-System für Agents |
| **Approval-Gate** (universal tool execution policy) | NomOS hat Approvals nur über DB-Tabelle, kein Runtime-Gate |

Wenn Atlas und NomOS v0.7.0 integrieren, könnten die besten Atlas-Patterns
in NomOS einwandern (nicht alle — Atlas bleibt internal-only).

---

## 5. Sicherheits-Implikationen

**Atlas + NomOS = grösserer Attack-Surface.**

- Atlas hard-coded `10.40.10.x` IPs **dürfen nicht in NomOS-Requests landen**. Atlas-Code-Audit nötig (`grep -rn "10\.40\.10"` in `src/main/`).
- Atlas's known RCE in `worker-agent/server.ts:68` **muss vor Integration gefixt sein**. Sonst kann NomOS-Audit-Trail durch einen Atlas-Compromise vergiftet werden.
- Atlas's Service-API-Key zu NomOS ist eine **neue Token-Klasse** — separate Vault-Path: `nomos/secrets/atlas-bridge`.
- Bei Atlas-Compromise: NomOS-side Rate-Limit muss greifen. Ein
  compromised Atlas könnte 10k Events/min schicken — Audit-Chain
  würde explodieren.
- **Fail-Safe Direction:** wenn Atlas-NomOS-Bridge down, **NomOS bleibt
  uneingeschränkt funktional** (NomOS ist nicht von Atlas abhängig).
  Atlas degradiert (cached verdicts, queued audit-events).

---

## 6. Realistische Timeline

| Phase | Inhalt | Aufwand |
|---|---|---|
| **v0.7.0-pre** | NomOS: Audit-Entry-Batch, EventType-Erweiterung, Cost-Endpoint | 2 Tage |
| **v0.7.0** | Atlas: NomOSAuditSink + NomOSComplianceClient, Settings-UI | 3 Tage |
| **v0.7.0-eval** | End-to-end-Run: Atlas-Agent hires/runs/crashes → komplette Compliance-Story in NomOS verfügbar | 1 Tag |
| **v0.7.1** | Sentinel-Gate-Tag im Audit-Eintrag, Auto-Learner-Hook | 1 Tag |

**Voraussetzung:** Atlas Phase 3.5 abgeschlossen + RCE gefixt
(Action Plan v2.0 lane). Atlas Phase 4 (Agent-Intelligence) muss
noch nicht abgeschlossen sein — Bridge funktioniert auch mit
Phase-3.5-Atlas.

---

## 7. Was passiert wenn NomOS nicht integriert wird (Null-Hypothese)

Joe nutzt Atlas für sich, NomOS verkauft an Customer. Beide
laufen parallel. **Compliance-Story für Joe selbst bleibt offen** —
Joe hat keine Annex-IV-Evidence für seine eigene Agent-Operation.
Wenn EU-AI-Act-Behörde fragt "Wie compliancen Sie Ihren eigenen
Use Case?" → kein Antwortpfad.

Integration ist also **strategisch wertvoll für Joe als Demonstration**:
"Wir essen unser eigenes Hundefutter. Atlas-Agents laufen unter
NomOS-Compliance. Hier ist die STH."

Plus: Atlas's Memory-Engine + Sentinel-Gate sind echte Features
die NomOS einbauen könnte als Customer-USP (über das hinaus, was
heute Standard ist).

---

## 8. Strategische Frage an Joe

**Soll Atlas das Pilot-Customer-Beispiel für NomOS werden?**

Wenn ja:
- Atlas wird nicht mehr nur internal-only — es wird "der erste NomOS-Customer"
- Atlas-Roadmap muss NomOS-Integration einplanen (heute nicht in Phase 4-5)
- Strategic Marketing: "Wir bauen Atlas auf NomOS — das ist unser
  eigenes Compliance-Audit"

Wenn nein:
- Bridge bleibt optional (opt-in via Settings-UI)
- Atlas bleibt Joe's Werkzeug, NomOS bleibt Customer-Produkt
- Compliance-Story für Joe-internal muss anders gelöst werden (manuelle Annex-IV)

**Empfehlung:** ja. Es ist die saubere "Bell-Labs-Selbstanwendung":
wir bauen das Werkzeug das wir selbst auch nutzen. Wenn unser
Customer-Compliance-Produkt nicht gut genug ist für unsere eigene
Agent-Fleet, dann ist es nicht gut genug für DACH-KMU.
