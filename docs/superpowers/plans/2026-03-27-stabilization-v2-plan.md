# NomOS Stabilisierung v2 — Contract Alignment, Console Truthfulness, Plugin Safety, Hygiene

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Frontend, Plugin und API auf identische Contracts bringen. Jede Console-Page zeigt nur was die API wirklich liefert. Plugin-Events muessen valide sein. Repo aufraumen. CI haerten. Doku aktualisieren.

**Architecture:** `nomos-api/nomos_api/schemas.py` ist die EINZIGE Wahrheit. `nomos-console/src/lib/types.ts` wird daraus abgeleitet. `nomos-plugin/src/api-client.ts` mappt API-Responses korrekt. `nomos-cli/nomos/core/events.py` definiert alle validen Event-Types. Jede Page die mehr zeigt als die API liefert wird zurueckgebaut.

**Tech Stack:** Python 3.12 (FastAPI, Pydantic v2, pytest), TypeScript strict (Next.js 15, vitest), nomos-plugin (vitest)

**Quelle:** Zeile-fuer-Zeile Analyse aller Dateien am 27.03.2026 + zwei unabhaengige Audits

---

## Referenz-Dateien

| Datei | Rolle |
|---|---|
| `nomos-api/nomos_api/schemas.py` | **WAHRHEIT** — alle Response-Schemas |
| `nomos-api/nomos_api/models.py` | **ORM** — DB-Struktur |
| `nomos-cli/nomos/core/events.py` | **WAHRHEIT** — valide Event-Types |
| `nomos-console/src/lib/types.ts` | **CONSUMER** — muss schemas.py spiegeln |
| `nomos-console/src/lib/auth.ts` | **CONSUMER** — Auth-Endpoints |
| `nomos-plugin/src/api-client.ts` | **CONSUMER** — muss schemas.py spiegeln |
| `.gsd/audits/2026-03-27-*` | Audit-Reports |

---

## Mismatch-Matrix (Analyseergebnis)

### types.ts vs schemas.py — Feld-fuer-Feld

| Interface | Feld | Frontend (types.ts) | Backend (schemas.py) | Aktion |
|---|---|---|---|---|
| `Agent` | `heartbeat_at` | FEHLT | `datetime \| None` | Hinzufuegen |
| `Agent` | `status` | `'running'\|'paused'\|'killed'\|'deploying'\|'error'` | hat auch `'created'\|'retired'` | Erweitern |
| `ComplianceMatrixCell` | ganzes Interface | per-document (14 Docs erfunden) | per-agent Summary | Ersetzen |
| `ComplianceMatrixResponse` | `agents, document_types, health_score` | existiert | FEHLT im Backend | Entfernen |
| `TaskEntry` | `title` | existiert | FEHLT (Backend hat `description`) | Entfernen |
| `TaskEntry` | `agent_name` | existiert | FEHLT im Backend | Entfernen |
| `TaskEntry` | `priority` | `'low'\|'medium'\|'high'\|'critical'` | `'low'\|'normal'\|'high'\|'urgent'` | Aendern |
| `TaskEntry` | `status` | fehlt `'failed'` | hat `'failed'` | Hinzufuegen |
| `TaskEntry` | `timeout_minutes, cost_eur` | FEHLT | existiert | Hinzufuegen |
| `TaskEntry` | `created_by` | `string` | `string \| null` | Aendern |
| `HeartbeatEntry` | ganzes Interface | existiert | Kein Endpoint | Loeschen |
| `DailyCostEntry` | ganzes Interface | existiert | Kein Endpoint | Loeschen |
| `CostDetailResponse` | ganzes Interface | existiert | API gibt `CostOverviewResponse` | Loeschen |
| `HealthStatus` | ganzes Interface | existiert | Kein Endpoint (nur `{status,service,version}`) | Loeschen |
| `HealthResponse` | `services?, uptime_seconds?` | existiert | FEHLT im Backend | Entfernen |
| `UserAccount` | `name` | editierbar | read-only (Backend default `""`) | Nur anzeigen |
| `UserAccount` | `max_tasks` | editierbar | read-only (Backend default `10`) | Nur anzeigen |
| `UserAccount` | `totp_enabled` | FEHLT | existiert | Hinzufuegen |
| `UserAccount` | `session_timeout_hours` | FEHLT | existiert | Hinzufuegen |

### Plugin api-client.ts vs schemas.py

| Methode | Plugin erwartet | API liefert | Aktion |
|---|---|---|---|
| `checkCompliance()` | `{ passed, missing[] }` | `ComplianceResponse { status, missing_documents[] }` | Response-Mapping |
| `filterPII()` | `{ filtered, found: {type, position[]}[] }` | `PIIFilterResponse { filtered, pii_count, matches: {type, start, end}[] }` | Response-Mapping |
| `checkBudget()` | `{ allowed, remaining }` | `{ allowed, status, remaining, percent_used, current, limit, agent_id }` | OK (Subset) |

### Plugin Event-Types vs events.py

| Plugin emittiert | In events.py? | Aktion |
|---|---|---|
| `tool.call_allowed` | JA | - |
| `tool.completed` | NEIN | Hinzufuegen |
| `message.ai_disclosure` | NEIN | Hinzufuegen |
| `session.started` | NEIN | Hinzufuegen |
| `session.ended` | NEIN | Hinzufuegen |
| `agent.ended` | NEIN | Hinzufuegen |
| `kill_switch.user_pause` | JA | - |

### Auth Route Drift

| Aktion | Frontend (auth.ts) | Backend (auth.py) | Aktion |
|---|---|---|---|
| 2FA Verify Route | `POST /auth/totp/verify` | `POST /api/auth/2fa/verify` | Frontend Route aendern |
| 2FA Verify Response | erwartet `{ user: MeResponse }` | gibt `{ verified: bool }` | Backend erweitern ODER Frontend /me fetch |
| Login Response | korrekt | korrekt | - |
| Logout | korrekt | korrekt | - |

### Console Pages — Truthfulness

| Page | Problem | Aktion |
|---|---|---|
| `admin/page.tsx:532` | `compliance_status === 'compliant'` | Aendern zu `'passed'` |
| `admin/team/[id]/page.tsx:160` | `compliance_status === 'compliant'` | Aendern zu `'passed'` |
| `admin/audit/page.tsx:108` | Hardcoded `{ data: null }` — kein Daten | Backend Global Audit Endpoint + real fetch |
| `admin/compliance/page.tsx:103` | 14 Document-Types erfunden, fake Matrix | Zurueckbauen auf per-agent Tabelle |
| `admin/tasks/page.tsx:191-196` | Sendet `title` statt `description`, `medium`/`critical` Prioritaeten | Korrigieren |
| `admin/users/page.tsx:135-141` | Sendet `name`, `max_tasks` — Backend akzeptiert nur `email, password, role` | Form reduzieren |
| `admin/costs/page.tsx:143` | Nutzt `CostDetailResponse` — API gibt `CostOverviewResponse` | Type aendern |
| `admin/settings/page.tsx:4` | Kommentar "API endpoints do not exist yet" — API existiert | Kommentar + Fallback entfernen |
| `app/tasks/page.tsx:41` | Nutzt `TaskEntry` mit falschen Feldern | Korrigieren nach Task-Fix |

---

## TEIL A: Contract Alignment (Backend + types.ts + Plugin)

### Task A1: types.ts — Agent Interface alignen

**Files:**
- Modify: `nomos-console/src/lib/types.ts:6-18`

**Was genau aendern:**

- [ ] Agent Interface korrigieren:
```typescript
export interface Agent {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  risk_class: 'minimal' | 'limited' | 'high';
  status: 'created' | 'running' | 'paused' | 'killed' | 'retired' | 'deploying' | 'error';
  manifest_hash: string;
  compliance_status: string;
  heartbeat_at: string | null;
  created_at: string;
  updated_at: string;
}
```

- [ ] `agentStatusToBadge` erweitern um `'created'` und `'retired'`:
```typescript
export function agentStatusToBadge(status: string): AgentBadgeStatus {
  switch (status) {
    case 'running': return 'online';
    case 'paused': return 'paused';
    case 'killed': return 'killed';
    case 'deploying': return 'deploying';
    case 'error': return 'error';
    case 'created': return 'deploying';
    case 'retired': return 'offline';
    default: return 'offline';
  }
}
```

- [ ] Verifizieren: `cd nomos-console && npx tsc --noEmit`
- [ ] Commit: `fix(types): Agent — add heartbeat_at, created/retired status`

---

### Task A2: types.ts — ComplianceMatrix alignen + Page zurueckbauen

**Files:**
- Modify: `nomos-console/src/lib/types.ts:119-135`
- Modify: `nomos-console/src/app/admin/compliance/page.tsx`

**Schritt 1: Types korrigieren**

- [ ] `ComplianceMatrixCell` ersetzen durch `ComplianceMatrixEntry`:
```typescript
/** Compliance matrix entry — per-agent summary from API. */
export interface ComplianceMatrixEntry {
  agent_id: string;
  agent_name: string;
  status: string;
  missing_docs: string[];
  risk_class: string;
}

/** Compliance matrix response from GET /api/compliance/matrix. */
export interface ComplianceMatrixResponse {
  matrix: ComplianceMatrixEntry[];
  total: number;
}
```

- [ ] Alten `ComplianceMatrixCell` Import aus compliance/page.tsx entfernen

**Schritt 2: compliance/page.tsx komplett vereinfachen**

- [ ] Entferne die gesamte `cellLookup` / `allDocs` / erfundene Matrix-Logik (Zeilen 93-114)
- [ ] Entferne `health_score` Anzeige (Backend liefert keinen health_score)
- [ ] Entferne `statusColors` Map (kein per-cell Status mehr)
- [ ] Entferne `statusLabel` Funktion
- [ ] Entferne Detail-Modal (kein per-document Detail mehr)
- [ ] Neue Page zeigt einfache Tabelle:

```tsx
// Import aendern
import type { ComplianceMatrixResponse, ComplianceMatrixEntry } from '@/lib/types';

// ComplianceContent Kern:
const data = matrix.data;
if (!data || data.matrix.length === 0) { /* Empty State */ }

// Einfache Tabelle
<table>
  <thead>
    <tr>
      <th>Agent</th>
      <th>{t('users.status', language)}</th>
      <th>{t('compliance.missingDocs', language)}</th>
      <th>Risk Class</th>
    </tr>
  </thead>
  <tbody>
    {data.matrix.map((entry: ComplianceMatrixEntry) => (
      <tr key={entry.agent_id}>
        <td>{entry.agent_name}</td>
        <td><Badge status={entry.status === 'passed' ? 'online' : 'error'} label={entry.status} /></td>
        <td>{entry.missing_docs.length === 0 ? '—' : entry.missing_docs.join(', ')}</td>
        <td><Badge label={entry.risk_class} /></td>
      </tr>
    ))}
  </tbody>
</table>
```

- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(compliance): align matrix with real API — no invented documents`

---

### Task A3: types.ts — TaskEntry alignen + Pages fixen

**Files:**
- Modify: `nomos-console/src/lib/types.ts:206-217`
- Modify: `nomos-console/src/app/admin/tasks/page.tsx`
- Modify: `nomos-console/src/app/app/tasks/page.tsx`

**Schritt 1: TaskEntry korrigieren**

- [ ] TaskEntry ersetzen:
```typescript
export interface TaskEntry {
  id: string;
  agent_id: string;
  description: string;
  status: 'queued' | 'assigned' | 'running' | 'review' | 'done' | 'failed';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_by: string | null;
  timeout_minutes: number;
  cost_eur: number;
  created_at: string;
  updated_at: string;
}
```

**Schritt 2: admin/tasks/page.tsx fixen**

- [ ] `TASK_STATUSES` erweitern um `'failed'`:
```typescript
const TASK_STATUSES: TaskEntry['status'][] = ['queued', 'assigned', 'running', 'review', 'done', 'failed'];
```

- [ ] `statusColumnLabel` erweitern:
```typescript
case 'failed': return t('tasks.failed', lang);
```

- [ ] `statusColumnColor` erweitern:
```typescript
case 'failed': return 'var(--color-error)';
```

- [ ] `priorityBadge` aendern (`medium` → `normal`, `critical` → `urgent`):
```typescript
function priorityBadge(priority: TaskEntry['priority']): BadgeStatus {
  switch (priority) {
    case 'urgent': return 'error';
    case 'high': return 'error';
    case 'normal': return 'paused';
    case 'low': return 'online';
  }
}
```

- [ ] `priorityLabel` aendern:
```typescript
function priorityLabel(priority: TaskEntry['priority'], lang: 'de' | 'en'): string {
  switch (priority) {
    case 'urgent': return t('tasks.priorityUrgent', lang);
    case 'high': return t('tasks.priorityHigh', lang);
    case 'normal': return t('tasks.priorityNormal', lang);
    case 'low': return t('tasks.priorityLow', lang);
  }
}
```

- [ ] `TaskCard`: Ersetze `task.title` durch `task.description` und `task.agent_name` durch `task.agent_id`:
```tsx
{/* Title durch Description ersetzen */}
<p className="text-sm font-semibold text-[var(--color-text)] line-clamp-2">{task.description}</p>
{/* agent_name durch agent_id ersetzen */}
<span className="text-[10px] text-[var(--color-muted)]">{task.agent_id}</span>
```

- [ ] `CreateTaskForm` Interface aendern:
```typescript
interface CreateTaskForm {
  description: string;
  agent_id: string;
  priority: TaskEntry['priority'];
}
```

- [ ] `handleCreate` aendern — `title` entfernen, `description` senden:
```typescript
await api.post('/tasks', {
  description: form.description,
  agent_id: form.agent_id || undefined,
  priority: form.priority,
});
```

- [ ] Form Initialisierung aendern:
```typescript
const [form, setForm] = useState<CreateTaskForm>({
  description: '',
  agent_id: '',
  priority: 'normal',
});
```

- [ ] Create-Modal: `title` Input entfernen, `description` als Hauptfeld, Priority-Options:
```tsx
<Select
  label={t('tasks.priority', language)}
  options={[
    { value: 'low', label: t('tasks.priorityLow', language) },
    { value: 'normal', label: t('tasks.priorityNormal', language) },
    { value: 'high', label: t('tasks.priorityHigh', language) },
    { value: 'urgent', label: t('tasks.priorityUrgent', language) },
  ]}
  ...
/>
```

- [ ] `handleCreate` Validierung aendern: `form.description.trim()` statt `form.title.trim()`
- [ ] Disabled-Check im Create-Button: `!form.description.trim()` statt `!form.title.trim()`

**Schritt 3: app/tasks/page.tsx gleiche Fixes**

- [ ] `taskStatusBadge` erweitern um `'failed'`
- [ ] Alle `task.title` Referenzen durch `task.description` ersetzen
- [ ] Priority im Create-Form von `'medium'` auf `'normal'` aendern
- [ ] Create-Body: `description` statt `title` senden

- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(tasks): align with real API — description not title, correct priority/status enums`

---

### Task A4: Speculative Types entfernen + betroffene Pages fixen

**Files:**
- Modify: `nomos-console/src/lib/types.ts`
- Modify: `nomos-console/src/app/admin/costs/page.tsx`
- Modify: `nomos-console/src/app/admin/diagnostics/page.tsx`

**Schritt 1: Speculative Types loeschen**

- [ ] `HeartbeatEntry` Interface loeschen (Zeilen 156-163)
- [ ] `DailyCostEntry` Interface loeschen (Zeilen 166-169)
- [ ] `CostDetailResponse` Interface loeschen (Zeilen 172-178)
- [ ] `HealthStatus` Interface loeschen (Zeilen 138-144)
- [ ] `HealthResponse` vereinfachen — nur was die API liefert:
```typescript
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}
```

**Schritt 2: costs/page.tsx fixen**

- [ ] Import aendern: `CostDetailResponse` → `CostOverviewResponse`
```typescript
import type { CostOverviewResponse, CostEntry } from '@/lib/types';
```
- [ ] `useFetch<CostDetailResponse>` → `useFetch<CostOverviewResponse>`
- [ ] `totalCost` berechnen als Summe:
```typescript
const totalCost = costEntries.reduce((sum, c) => sum + c.total_cost_eur, 0);
```
- [ ] `daily_trend` Chart komplett entfernen (Backend hat kein daily_trend):
  - Loeschen: `DailyTrendChart` Komponente
  - Loeschen: `dailyTrend` Variable
  - Loeschen: Chart-Rendering Block (Zeilen 224-235)

**Schritt 3: diagnostics/page.tsx fixen**

Die Page importiert `HealthStatus` (wird geloescht) und nutzt `healthData.services` + `healthData.uptime_seconds` (existieren nicht in API).

- [ ] Import aendern — `HealthStatus` entfernen:
```typescript
// ALT:
import type { HealthResponse, HealthStatus, FleetResponse } from '@/lib/types';
// NEU:
import type { HealthResponse, FleetResponse } from '@/lib/types';
```

- [ ] `ServiceCard` Komponente loeschen (nutzt `HealthStatus` Type)
- [ ] `ResourceBar` Komponente loeschen (nutzt `HeartbeatEntry`-artige Daten die nicht existieren)
- [ ] `formatUptime` Funktion loeschen (`uptime_seconds` existiert nicht)

- [ ] Overall Status Card vereinfachen — nur Status + Version:
```tsx
{healthData && (
  <Card>
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Badge
          status={healthBadgeStatus(healthData.status)}
          label={healthLabel(healthData.status, language)}
        />
        <span className="text-sm text-[var(--color-text)] font-semibold">
          {healthData.service}
        </span>
      </div>
      <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
        v{healthData.version}
      </span>
    </div>
  </Card>
)}
```

- [ ] Services-Section ersetzen — da API keine Services-Liste liefert, zeige Hinweis:
```tsx
<Card>
  <CardHeader title={t('diagnostics.services', language)} />
  <p className="text-sm text-[var(--color-muted)] mt-2">
    {t('diagnostics.singleServiceHealth', language)}
  </p>
</Card>
```

- [ ] Heartbeat Board bleibt — nutzt Fleet-Daten (`agent.updated_at`), das ist korrekt
- [ ] Ersetze `agent.updated_at` durch `agent.heartbeat_at` (nach A1 verfuegbar):
```tsx
<span className="font-semibold">{t('diagnostics.lastSeen', language)}:</span>{' '}
{agent.heartbeat_at ? formatDate(agent.heartbeat_at, language) : '—'}
```

**Schritt 4: costs/page.tsx fixen (ehemals Task B5)**

- [ ] Import aendern: `CostDetailResponse` → `CostOverviewResponse`
```typescript
import type { CostOverviewResponse, CostEntry } from '@/lib/types';
```
- [ ] `useFetch<CostDetailResponse>` → `useFetch<CostOverviewResponse>`
- [ ] `totalCost` berechnen als Summe (nicht aus `data?.total_cost_eur`):
```typescript
const totalCost = costEntries.reduce((sum, c) => sum + c.total_cost_eur, 0);
```
- [ ] `DailyTrendChart` Komponente komplett loeschen (Backend hat kein `daily_trend`)
- [ ] `dailyTrend` Variable und Chart-Rendering Block loeschen (Zeilen 183, 224-235)

- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(types): remove speculative types — HeartbeatEntry, CostDetailResponse, HealthStatus + fix costs/diagnostics pages`

---

### Task A5: Auth 2FA Route + Response fixen

**Files:**
- Modify: `nomos-console/src/lib/auth.ts:121`
- Modify: `nomos-api/nomos_api/routers/auth.py`
- Modify: `nomos-api/nomos_api/schemas.py:133-134`
- Test: `nomos-api/tests/test_auth_router.py`

**Entscheidung:** Backend erweitern — nach TOTP Verify den User zurueckgeben. Einfacher als Frontend-Workaround.

**Schritt 1: Backend erweitern**

- [ ] `schemas.py` — `TotpVerifyResponse` erweitern:
```python
class TotpVerifyResponse(BaseModel):
    verified: bool
    user: LoginUserInfo | None = None
```

- [ ] `routers/auth.py` — In der `verify_2fa` Funktion: Nach erfolgreichem Verify den User mitgeben:
```python
# Nach der Zeile die verified=True setzt:
return TotpVerifyResponse(
    verified=True,
    user=LoginUserInfo(
        id=user.id,
        email=user.email,
        name="",  # User model hat kein name-Feld
        role=user.role,
    ),
)
```

- [ ] Test schreiben:
```python
async def test_2fa_verify_returns_user(client, db_session):
    # Setup: User mit TOTP erstellen, Code generieren
    # Act: POST /api/auth/2fa/verify
    # Assert: response.verified == True AND response.user.email == expected
```

- [ ] Tests ausfuehren: `cd nomos-api && uv run pytest tests/test_auth_router.py -v`

**Schritt 2: Frontend Route aendern**

- [ ] `auth.ts:121` — Route aendern:
```typescript
// ALT:
const response = await api.post<{ user: MeResponse }>('/auth/totp/verify', { code });
// NEU:
const response = await api.post<{ verified: boolean; user?: MeResponse }>('/auth/2fa/verify', { code });
if (response.user) {
  setUser({
    id: response.user.id,
    email: response.user.email,
    name: response.user.name,
    role: response.user.role,
  });
}
```

- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(auth): align 2FA route /auth/2fa/verify + return user in response`

---

### Task A6: Plugin api-client.ts Response-Mapping fixen

**Files:**
- Modify: `nomos-plugin/src/api-client.ts`
- Modify: `nomos-plugin/src/hooks/before-agent-start.ts`
- Modify: `nomos-plugin/tests/api-client.test.ts`
- Modify: `nomos-plugin/tests/helpers/mock-api.ts`
- Modify: `nomos-plugin/tests/hooks/before-agent-start.test.ts`

**Schritt 1: ComplianceResult Interface + checkCompliance() fixen**

- [ ] `ComplianceResult` bleibt (ist das interne Plugin-Format)
- [ ] `checkCompliance()` Response-Mapping hinzufuegen:
```typescript
async checkCompliance(agentId: string): Promise<ComplianceResult> {
  try {
    const res = await fetch(`${this.baseUrl}/api/compliance/gate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent_id: agentId }),
    });
    if (!res.ok) return { passed: false, missing: [], error: `HTTP ${res.status}` };
    const data = await res.json();
    // API returns ComplianceResponse { status, missing_documents, errors, warnings }
    // Map to internal ComplianceResult format
    return {
      passed: data.status === "passed",
      missing: data.missing_documents ?? [],
      error: data.errors?.length > 0 ? data.errors.join(", ") : undefined,
    };
  } catch (err) {
    return { passed: false, missing: [], error: String(err) };
  }
}
```

**Schritt 2: PIIFilterResult Interface + filterPII() fixen**

- [ ] `PIIFilterResult` Interface aendern:
```typescript
export interface PIIFilterResult {
  filtered: string;
  pii_count: number;
  matches: Array<{ type: string; start: number; end: number }>;
}
```

- [ ] `filterPII()` Fallback aendern:
```typescript
catch {
  return { filtered: text, pii_count: 0, matches: [] };
}
```

**Schritt 3: Tests anpassen**

- [ ] `tests/helpers/mock-api.ts` — Compliance Mock-Response:
```typescript
// ALT: { passed: true, missing: [] }
// NEU: { status: "passed", missing_documents: [], errors: [], warnings: [] }
```

- [ ] `tests/helpers/mock-api.ts` — PII Mock-Response:
```typescript
// ALT: { filtered, found }
// NEU: { filtered, pii_count, matches }
```

- [ ] `tests/api-client.test.ts` — Assertions anpassen
- [ ] `tests/hooks/before-agent-start.test.ts` — Mock anpassen auf `{ status: "passed", ... }`

**Schritt 4: Build + Test**

- [ ] Plugin bauen: `cd nomos-plugin && npm run build`
- [ ] Plugin Tests: `cd nomos-plugin && npx vitest run`
- [ ] Commit: `fix(plugin): align api-client with real backend response schemas`

---

### Task A7: Plugin Event-Types in events.py registrieren

**Files:**
- Modify: `nomos-cli/nomos/core/events.py:15-79`
- Test: `nomos-cli/tests/test_events.py`

**Problem:** Plugin emittiert 5 Event-Types die nicht in `events.py` registriert sind. Die `validate_event_type()` Funktion in `routers/audit.py` blockiert diese Events — **Audit-Eintraege gehen verloren!**

- [ ] Neue Event-Types zu `EventType` Enum hinzufuegen:
```python
class EventType(str, Enum):
    # ... existing ...

    # Tool Calls (from Plugin hooks)
    TOOL_CALL_ALLOWED = "tool.call_allowed"
    TOOL_CALL_BLOCKED = "tool.call_blocked"
    TOOL_COMPLETED = "tool.completed"  # NEU

    # Messages
    MESSAGE_AI_DISCLOSURE = "message.ai_disclosure"  # NEU

    # Sessions (from Plugin hooks)
    SESSION_STARTED = "session.started"  # NEU
    SESSION_ENDED = "session.ended"  # NEU

    # Agent lifecycle
    AGENT_CREATED = "agent.created"
    AGENT_DEPLOYED = "agent.deployed"
    AGENT_STOPPED = "agent.stopped"
    AGENT_RETIRED = "agent.retired"
    AGENT_ENDED = "agent.ended"  # NEU
```

- [ ] Test schreiben:
```python
def test_plugin_event_types_are_valid():
    """All event types emitted by the plugin must be registered."""
    plugin_events = [
        "tool.call_allowed",
        "tool.completed",
        "message.ai_disclosure",
        "session.started",
        "session.ended",
        "agent.ended",
        "kill_switch.user_pause",
    ]
    for event in plugin_events:
        assert validate_event_type(event), f"Plugin event {event!r} not registered"
```

- [ ] Tests ausfuehren: `cd nomos-cli && uv run pytest tests/test_events.py -v`
- [ ] Commit: `fix(events): register plugin event types — tool.completed, session.started/ended, etc.`

---

## TEIL B: Console Truthfulness

### Task B1: Global Audit Endpoint + Page fixen

**Files:**
- Modify: `nomos-api/nomos_api/routers/audit.py`
- Modify: `nomos-console/src/app/admin/audit/page.tsx`
- Modify: `nomos-console/src/app/admin/page.tsx` (Dashboard Activity Feed)
- Test: `nomos-api/tests/test_audit.py`

**Schritt 1: Backend — GET /api/audit Endpoint**

- [ ] In `routers/audit.py` neuen Endpoint hinzufuegen:
```python
@router.get("/audit", response_model=AuditResponse)
async def get_global_audit(
    limit: int = 100,
    offset: int = 0,
    agent_id: str | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Global audit trail — aggregates all agents with optional filters."""
    query = select(AuditLog).order_by(AuditLog.id.desc())
    if agent_id:
        query = query.where(AuditLog.agent_id == agent_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)

    # Count total
    from sqlalchemy import func
    count_query = select(func.count()).select_from(AuditLog)
    if agent_id:
        count_query = count_query.where(AuditLog.agent_id == agent_id)
    if event_type:
        count_query = count_query.where(AuditLog.event_type == event_type)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    entries = result.scalars().all()

    return AuditResponse(
        agent_id="*",  # Global
        entries=[
            AuditEntryResponse(
                sequence=e.sequence,
                event_type=e.event_type,
                agent_id=e.agent_id,
                data=e.data or {},
                chain_hash=e.chain_hash,
                timestamp=e.timestamp,
            )
            for e in entries
        ],
        total=total,
    )
```

- [ ] Test:
```python
async def test_global_audit_endpoint(client, db_session):
    response = await client.get("/api/audit")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data

async def test_global_audit_filter_by_agent(client, db_session):
    response = await client.get("/api/audit?agent_id=test-agent")
    assert response.status_code == 200
```

- [ ] Tests ausfuehren: `cd nomos-api && uv run pytest tests/test_audit.py -v`

**Schritt 2: Audit Page fixen**

- [ ] Hardcoded empty ersetzen durch echten Fetch:
```typescript
// ALT (Zeile 108):
const auditFetch = { data: null, loading: false, error: null, reload: () => {} };
// NEU:
const auditFetch = useFetch<AuditResponse>('/audit');
```

- [ ] Verify-Button auf echte API umstellen:
```typescript
const handleVerifyChain = useCallback(async () => {
  if (!agentFilter) {
    addToast({ type: 'warning', message: t('audit.selectAgentToVerify', language), duration: 4000 });
    return;
  }
  setVerifying(true);
  try {
    const result = await api.get<{ valid: boolean; entries_checked: number; errors: string[] }>(
      `/audit/verify/${agentFilter}`
    );
    addToast({
      type: result.valid ? 'success' : 'warning',
      message: result.valid
        ? t('audit.chainValid', language)
        : `${t('audit.chainInvalid', language)}: ${result.errors.join(', ')}`,
      duration: 5000,
    });
  } catch (err) {
    const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
    addToast({ type: 'error', message: msg, duration: 6000 });
  } finally {
    setVerifying(false);
  }
}, [agentFilter, language, addToast]);
```

- [ ] Export-Button auf echte API umstellen (fuer JSONL):
```typescript
const handleExport = useCallback((format: 'jsonl' | 'pdf') => {
  if (format === 'jsonl') {
    if (agentFilter) {
      // Use real backend export endpoint for selected agent
      window.open(`/api/agents/${agentFilter}/audit/export`, '_blank');
    } else {
      // Client-side export from currently loaded global data
      const lines = filteredEntries.map((entry) => JSON.stringify(entry)).join('\n');
      const blob = new Blob([lines], { type: 'application/x-jsonlines' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomos-audit-${new Date().toISOString().slice(0, 10)}.jsonl`;
      a.click();
      URL.revokeObjectURL(url);
    }
  } else {
    addToast({ type: 'info', message: t('toast.exportStarted', language), duration: 3000 });
  }
}, [agentFilter, filteredEntries, language, addToast]);
```

**Schritt 3: Dashboard Activity Feed fixen**

- [ ] `admin/page.tsx:516` — Hardcoded null ersetzen:
```typescript
// ALT:
const audit = { data: null as { entries: AuditEntry[] } | null, loading: false, error: null };
// NEU:
const audit = useFetch<{ entries: AuditEntry[]; total: number }>('/audit?limit=10');
```

- [ ] `tsc --noEmit` pass
- [ ] Commit: `feat(audit): global audit endpoint + real verification + dashboard activity feed`

---

### Task B2: Compliance Status Semantik

**Files:**
- Modify: `nomos-console/src/app/admin/page.tsx:532`
- Modify: `nomos-console/src/app/admin/team/[id]/page.tsx:160`
- Modify: `nomos-console/src/app/admin/team/page.tsx:74`

- [ ] In `admin/page.tsx:532`:
```typescript
// ALT:
const compliantCount = agents.filter((a) => a.compliance_status === 'compliant').length;
// NEU:
const compliantCount = agents.filter((a) => a.compliance_status === 'passed').length;
```

- [ ] In `admin/team/[id]/page.tsx:160`:
```typescript
// ALT:
const isCompliant = agent.compliance_status === 'compliant';
// NEU:
const isCompliant = agent.compliance_status === 'passed';
```

- [ ] In `admin/team/page.tsx:74`:
```typescript
// ALT:
const isCompliant = agent.compliance_status === 'compliant';
// NEU:
const isCompliant = agent.compliance_status === 'passed';
```

- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(console): compliance_status 'passed' not 'compliant'`

---

### Task B3: Users Create/Edit Form alignen

**Files:**
- Modify: `nomos-console/src/app/admin/users/page.tsx`

**Schritt 1: Form Data Interface reduzieren**

- [ ] `UserFormData` fuer Create:
```typescript
interface UserCreateFormData {
  email: string;
  password: string;
  role: 'admin' | 'user' | 'officer';
}
```

- [ ] `UserFormData` fuer Edit:
```typescript
interface UserEditFormData {
  role: 'admin' | 'user' | 'officer';
  session_timeout_hours: number;
  is_active: boolean;
}
```

**Schritt 2: Create-Modal anpassen**

- [ ] Entferne `name` Input (Backend akzeptiert es nicht bei Create)
- [ ] Entferne `max_tasks` Input (Backend akzeptiert es nicht bei Create)
- [ ] Create-Body: Nur `{ email, password, role }` senden
- [ ] Validierung: Nur email + password pruefen

**Schritt 3: Edit-Modal anpassen**

- [ ] Entferne `name`, `email`, `password`, `max_tasks` aus Edit-Form
- [ ] Edit zeigt nur: `role` Dropdown, `session_timeout_hours` Input, `is_active` Toggle
- [ ] Edit-Body: Nur `{ role, session_timeout_hours, is_active }` senden

**Schritt 4: UserAccount Type updaten**

- [ ] In `types.ts` — `UserAccount` erweitern:
```typescript
export interface UserAccount {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'officer';
  totp_enabled: boolean;
  session_timeout_hours: number;
  is_active: boolean;
  max_tasks: number;
  allowed_agents: string[];
  created_at: string;
}
```

- [ ] User-Liste: `max_tasks` nur anzeigen (nicht editierbar)
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(users): align create/edit forms with backend UserCreateRequest/UserUpdateRequest`

---

### Task B4: Settings Page — Hardcoded Defaults entfernen

**Files:**
- Modify: `nomos-console/src/app/admin/settings/page.tsx`

- [ ] Kommentar `"API endpoints do not exist yet"` in Zeile 4-5 entfernen/aktualisieren
- [ ] `defaultSettings` Konstante loeschen (Zeile 24-28)
- [ ] `fromApi` State loeschen
- [ ] Manuellen `useEffect` (Zeilen 90-113) ersetzen durch `useFetch`:

```typescript
import { useFetch } from '@/lib/hooks';
// ... andere imports bleiben ...

function SettingsContent() {
  const { language } = useNomosStore();
  const settings = useFetch<SystemSettings>('/settings');

  if (settings.loading) {
    return <SettingsSkeleton />;
  }

  if (settings.error || !settings.data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">{settings.error ?? t('error.serverError', language)}</p>
          <Button variant="secondary" onClick={settings.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const config = settings.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('settings.description', language)}</p>
      </div>

      {/* Read-only notice */}
      <div
        className="flex items-center gap-3 px-4 py-3 bg-[var(--color-warning-light)] border border-[var(--color-warning)] rounded-[var(--radius)] text-sm text-[var(--color-text)]"
        role="status"
      >
        <svg className="w-5 h-5 text-[var(--color-warning)] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{t('settings.readOnly', language)}</span>
      </div>

      {/* Connection section */}
      <Card>
        <CardHeader title={t('settings.section.gateway', language)} />
        <div className="mt-2">
          <SettingsField label={t('settings.gatewayUrl', language)} value={config.gateway_url} />
        </div>
      </Card>

      {/* Data management section */}
      <Card>
        <CardHeader title={t('settings.section.data', language)} />
        <div className="mt-2">
          <SettingsField
            label={t('settings.retentionDays', language)}
            value={`${config.retention_days} ${language === 'de' ? 'Tage' : 'days'}`}
          />
        </div>
      </Card>

      {/* Privacy section */}
      <Card>
        <CardHeader title={t('settings.section.privacy', language)} />
        <div className="mt-2">
          <SettingsField
            label={t('settings.piiFilterMode', language)}
            value={piiModeLabel(config.pii_filter_mode, language)}
            badge={{
              status: piiModeBadge(config.pii_filter_mode),
              label: config.pii_filter_mode.toUpperCase(),
            }}
          />
        </div>
      </Card>
    </div>
  );
}
```

- [ ] Entferne `useState` und `useEffect` Imports (nicht mehr benoetigt fuer Settings-State)
- [ ] Entferne `api` Import (useFetch nutzt es intern)
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(settings): use real API data via useFetch, remove hardcoded defaults`

---

### ~~Task B5: Costs Page~~ (MERGED into A4 Step 4)

---

## TEIL C: Hygiene, CI, Doku, Learnings

### Task C1: .gitignore + Repo aufraumen

**Files:**
- Modify: `.gitignore`

- [ ] `.gitignore` ergaenzen:
```gitignore
# Claude Code / MCP / Tools
.claude/worktrees/
.bg-shell/
.gsd/
.playwright-mcp/

# Archive (historisch, nicht aktiv)
_archive/

# Build artifacts
tsconfig.tsbuildinfo
```

- [ ] Aus Git entfernen (lokal behalten):
```bash
git rm -r --cached .claude/worktrees/ 2>/dev/null || true
git rm -r --cached _archive/ 2>/dev/null || true
```

- [ ] Commit: `chore: gitignore cleanup — remove archive, tool artifacts from tracking`

---

### Task C2: CI haerten

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] Zeile 45: `continue-on-error: true` bei Console typecheck ENTFERNEN
- [ ] Zeile 135: `continue-on-error: true` bei Console tests ENTFERNEN
- [ ] S9 Check (Zeile 164): Console src hinzufuegen:
```yaml
if grep -rn "TODO\|FIXME\|HACK\|coming soon\|placeholder" \
  nomos-plugin/src/ nomos-console/src/ 2>/dev/null; then
```
- [ ] CI Summary (Zeilen 225-230): Korrekte Job-Referenzen:
```yaml
echo "| CLI Tests | ${{ needs.test-cli.result == 'success' && '✅' || '❌' }} |" >> $GITHUB_STEP_SUMMARY
echo "| API Tests | ${{ needs.test-api.result == 'success' && '✅' || '❌' }} |" >> $GITHUB_STEP_SUMMARY
echo "| Plugin Tests | ${{ needs.test-plugin.result == 'success' && '✅' || '❌' }} |" >> $GITHUB_STEP_SUMMARY
echo "| Console Tests | ${{ needs.test-console.result == 'success' && '✅' || '❌' }} |" >> $GITHUB_STEP_SUMMARY
```
- [ ] `ci-summary` needs aktualisieren:
```yaml
needs: [lint-python, lint-typescript, test-cli, test-api, test-plugin, test-console, quality-gate, docker-build]
```

- [ ] Commit: `fix(ci): remove continue-on-error, fix summary references, add console to S9 check`

---

### Task C3: Dokumentation aktualisieren

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/api-reference.md`

**README.md:**
- [ ] Feature-Liste aktualisieren: 17 Router, 20 Console Pages, 770+ Tests
- [ ] Tech Stack aktuell: PostgreSQL + Valkey + OpenClaw Gateway
- [ ] Quick Start: `docker compose up -d` + Login
- [ ] FCL Erklaerung: 3 Agents gratis, ab 4 kommerziell

**architecture.md:**
- [ ] Alle 17 Router dokumentieren (nicht nur 5)
- [ ] Alle 8 ORM Models dokumentieren
- [ ] Auth-Flow beschreiben (JWT Cookie + Plugin API Key + 2FA)
- [ ] Console → API → Gateway → LLM Pipeline

**api-reference.md:**
- [ ] Alle 47+ Endpoints dokumentieren (aktuell nur 8)
- [ ] Pro Endpoint: Method, Path, Auth, Request, Response
- [ ] Gruppiert nach Domain (Agent, Auth, Compliance, Audit, ...)

- [ ] Commit: `docs: refresh README, architecture, API reference to v2 reality`

---

### Task C4: CLAUDE.md Learnings dokumentieren

**Files:**
- Modify: `.claude/CLAUDE.md`

- [ ] Neue Regel hinzufuegen:
```markdown
## Learnings (27.03.2026)

1. **Types von API ableiten, nicht erfinden** — Frontend-Types die nicht zur API passen crashen React
2. **Nicht raten, Doku lesen** — OpenClaw Endpoints, NVIDIA Model-Namen, Gateway Config
3. **Kein Feature auf Fake-Fundament** — 8 In-Memory Services haben alles instabil gemacht
4. **Ein Feld-Mismatch = ein Crash** — `title` statt `description`, `compliant` statt `passed`
5. **Rate Limiter ist In-Memory** — bei API-Restart reset, bei zu vielen Tests lockt man sich selbst aus
6. **`is_active = false` unsichtbar** — User deaktiviert → Login 401 ohne klare Fehlermeldung
7. **Next.js rewrites sind Build-time** — `NOMOS_API_URL` muss beim Build gesetzt werden
8. **Windows Bind-Mounts = mode 777** — OpenClaw blockiert world-writable Plugins
9. **Plugin Event-Types muessen registriert sein** — audit.py validiert, unbekannte Events werden abgelehnt
```

- [ ] Link zum Stabilisierungsplan:
```markdown
## Aktiver Plan
- Stabilisierung: `docs/superpowers/plans/2026-03-27-stabilization-v2-plan.md`
```

- [ ] Commit: `docs: CLAUDE.md learnings + active plan reference`

---

## Abhaengigkeiten und Ausfuehrungsreihenfolge

**WICHTIG fuer parallele Ausfuehrung:** Tasks A1, A2, A3 aendern alle `types.ts`. Wenn sie von parallelen Subagenten ausgefuehrt werden, MUESSEN die types.ts-Aenderungen serialisiert werden (z.B. A1 zuerst committen, dann A2, dann A3). Alternativ: Ein Agent macht alle drei Type-Aenderungen in einem Task.

```
Phase 1 (parallel — keine Abhaengigkeiten):
  A1 (Agent types)      ─┐
  A2 (ComplianceMatrix)  ├── ACHTUNG: A1-A3 teilen types.ts → serialisieren!
  A3 (Tasks)             ├──
  A5 (Auth 2FA)          ├── Backend + Frontend, unabhaengig
  A6 (Plugin api-client) ├── Nur nomos-plugin/
  A7 (Plugin events)     ├── Nur nomos-cli/
  C1 (gitignore)         ┘

Phase 2 (nach Phase 1 — braucht korrigierte types.ts):
  A4 (Speculative Types + Costs Page + Diagnostics Page)

Phase 3 (nach Phase 2 — Pages nutzen korrigierte Types):
  B1 (Global Audit)     ─┐
  B2 (Compliance Status) ├── parallel ausfuehrbar
  B3 (Users Form)        ├── Alle aendern nur eigene Page
  B4 (Settings)          ┘

Phase 4 (nach Phase 3 — Doku basiert auf finalem Stand):
  C2 (CI)           ─┐
  C3 (Doku)          ├── parallel
  C4 (Learnings)     ┘
```

**Zusammenfassung:** 14 Tasks (B5 merged in A4), 4 Phasen. Phase 1 hat 7 Tasks (A1-A3 serialisiert auf types.ts). Phase 2 hat 1 Task. Phase 3 hat 4 parallele Tasks. Phase 4 hat 3 parallele Tasks.

---

## Verifikation nach Abschluss

- [ ] `cd nomos-console && npx tsc --noEmit` — 0 Errors
- [ ] `cd nomos-plugin && npm run build && npx vitest run` — alle Tests pass
- [ ] `cd nomos-api && uv run pytest -v` — alle Tests pass
- [ ] `cd nomos-cli && uv run pytest -v` — alle Tests pass
- [ ] `docker compose build` — baut ohne Fehler
- [ ] Jede Console Page in Browser mit F12 offen testen — 0 Errors
- [ ] Kein `TODO`, `FIXME`, `placeholder` in Produkt-Code
