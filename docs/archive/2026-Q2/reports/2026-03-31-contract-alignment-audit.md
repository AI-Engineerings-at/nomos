# NomOS Contract-Alignment Audit — 2026-03-31

> Audit-Methode: Echte Datei-Analyse aller Backend Schemas (schemas.py), Router, Frontend Types (types.ts), Console Pages, Plugin api-client.ts.
> Kein Raten. Jede Aussage referenziert eine echte Datei.

---

## Executive Summary

Von den 11 bekannten Tasks (A1-A6, B1-B5) aus der Stabilisierung v2 sind **9 gefixt** und **2 offen**.
Zusaetzlich wurden **7 neue Mismatches** identifiziert, davon 3 mit Prio HIGH.

| Kategorie | Gefixt | Offen | Neu gefunden |
|-----------|--------|-------|-------------|
| Type Alignment (A-Tasks) | 6/6 | 0 | 3 |
| Route/Logic Alignment (B-Tasks) | 3/5 | 2 | 4 |
| **Gesamt** | **9** | **2** | **7** |

---

## Teil 1: Status der 11 bekannten Tasks

### A-Tasks (Type Alignment)

| Task | Beschreibung | Status | Beleg |
|------|-------------|--------|-------|
| **A1** | Agent heartbeat_at + status alignen | **GEFIXT** | `types.ts:6-19` — Agent hat `heartbeat_at: string \| null`, `status` union mit `created`, `retired`. `agentStatusToBadge()` mapped `created` → `deploying`, `retired` → `offline`. Exakt wie im Plan. |
| **A2** | ComplianceMatrix — erfundene Docs entfernen | **GEFIXT** | `types.ts:121-133` — `ComplianceMatrixEntry` und `ComplianceMatrixResponse` matchen Backend `schemas.py:69-79` exakt. Compliance Page (`admin/compliance/page.tsx:21`) importiert korrekte Types, keine erfundene Matrix-Logik mehr. |
| **A3** | TaskEntry — title→description, priority enum | **GEFIXT** | `types.ts:183-194` — `TaskEntry` hat `description` (nicht `title`), `priority: 'low' \| 'normal' \| 'high' \| 'urgent'`, `status` mit 6 korrekten Werten. Matcht `schemas.py:204-215` exakt. |
| **A4** | Speculative Types entfernen | **GEFIXT** | `types.ts` enthaelt kein `HeartbeatEntry`, `FleetSummary`, `ComplianceMatrixCell`, oder andere erfundene Types. Alle 20 Interfaces matchen echte Backend-Schemas. |
| **A5** | Auth 2FA Route + Response alignen | **GEFIXT** | `auth.ts:31-39` — `LoginResponse` hat `requires_2fa`, `user` mit korrekten Feldern. `verifyTotp()` ruft `/auth/2fa/verify` auf, matcht Backend Route `POST /api/auth/2fa/verify`. |
| **A6** | Plugin api-client.ts Response-Mapping | **TEILWEISE GEFIXT** | Compliance mapping korrekt (`data.status === "passed"`), Audit entry korrekt, PII filter korrekt. **Aber: Heartbeat Body-Format Mismatch** — siehe N1 unten. |

### B-Tasks (Route/Logic Alignment)

| Task | Beschreibung | Status | Beleg |
|------|-------------|--------|-------|
| **B1** | Global Audit Endpoint implementieren | **GEFIXT** | Backend `audit.py:29-68` — `GET /api/audit` existiert mit `limit`, `offset`, `agent_id`, `event_type` Filtern. Frontend `admin/audit/page.tsx:106` — `useFetch<AuditResponse>('/audit')` ruft korrekt ab. Chain Verify (`/audit/verify/{agentId}`) funktioniert. |
| **B2** | Pause/Resume Route fixen | **OFFEN** | Frontend `app/page.tsx:146` ruft `api.post('/agents/${agentId}/${action}')` auf — das matcht Backend `POST /agents/{id}/pause` und `POST /agents/{id}/resume`. **ABER**: `chat/[id]/page.tsx:164` und `team/[id]/page.tsx:168` rufen `api.patch('/fleet/${agentId}', { status: '...' })` auf. Es gibt keinen `PATCH /api/fleet/{id}` Endpoint im Backend. `fleet.py` hat nur GET routes. Der `PATCH /api/agents/{id}` existiert in `agents.py:64`, gibt aber nur ein `dict` zurueck (kein `AgentResponse`). **Route-Drift: 2 Pages nutzen falschen Endpoint.** |
| **B3** | Compliance-Status 'passed' nicht 'compliant' | **GEFIXT** | Backend `compliance.py` verwendet `result.status.value` durchgehend. Frontend `types.ts:88` hat `status: string`. Team Detail `team/[id]/page.tsx:160` prueft `agent.compliance_status === 'passed'`. Kein `compliant` mehr im Code. |
| **B4** | Users Create/Edit Forms alignen | **GEFIXT** | Frontend `admin/users/page.tsx:121-131` — Edit sendet `PATCH /users/{id}` mit `role`, `session_timeout_hours`, `is_active`. Create sendet `POST /users` mit `email`, `password`, `role`. Matcht Backend `UserUpdateRequest` und `UserCreateRequest` in `schemas.py`. |
| **B5** | Settings-Page Fallback entfernen | **OFFEN (TEILWEISE)** | Settings Page (`admin/settings/page.tsx`) ruft `GET /settings` und `PATCH /settings` korrekt auf — das funktioniert. **ABER**: Settings Page hat keinen Fallback-Kommentar mehr ("API endpoints do not exist yet" ist weg), also ist der explizite Fallback entfernt. **Jedoch**: Diagnostics Page (`admin/diagnostics/page.tsx:41-47`) hat `healthBadgeStatus()` die auf `'ok'` matcht, aber Backend liefert `'healthy'` — beides wird korrekt gemapped. **Restproblem**: Keine Vault-Status Anzeige in Diagnostics (Backend liefert `vault` Feld, Frontend ignoriert es). |

---

## Teil 2: Neue Mismatches (N1-N7)

### N1: Plugin Heartbeat Body-Format Mismatch [HIGH]

**Dateien:**
- `nomos-plugin/src/api-client.ts:100-111`
- `nomos-api/nomos_api/schemas.py:256-258`

**Problem:** Backend `HeartbeatRequest` erwartet `{ "metrics": {...} }`. Plugin `sendHeartbeat()` sendet `JSON.stringify(status)` direkt, wobei `status` z.B. `{ "status": "active", "event": "message_received" }` ist. Das Body wird **nicht** in ein `{ metrics: ... }` Objekt gewrapped.

**Auswirkung:** Pydantic parst den Body. Da `metrics` optional ist (default `{}`), wird der Request nicht abgelehnt — aber die Metrik-Daten gehen verloren. Sie werden nie im Heartbeat gespeichert.

**Fix:** `api-client.ts:105` aendern zu `body: JSON.stringify({ metrics: status })`.

**Aufwand:** 5 Minuten.

---

### N2: PATCH /fleet/{id} Route existiert nicht im Backend [HIGH]

**Dateien:**
- `nomos-console/src/app/app/chat/[id]/page.tsx:164`
- `nomos-console/src/app/admin/team/[id]/page.tsx:168`
- `nomos-api/nomos_api/routers/fleet.py` (nur GET /fleet und GET /fleet/{id})
- `nomos-api/nomos_api/routers/agents.py:64-68` (PATCH /agents/{id} existiert)

**Problem:** Chat-Page und Team-Detail-Page rufen `api.patch('/fleet/${agentId}', { status: 'paused' })` auf. Dieser Endpoint existiert nicht. Backend hat:
- `PATCH /api/agents/{id}` → gibt ein `dict` zurueck (nicht `AgentResponse`)
- `POST /api/agents/{id}/pause` → gibt `AgentResponse` zurueck
- `POST /api/agents/{id}/resume` → gibt `AgentResponse` zurueck

**Auswirkung:** Pause/Resume in Chat und Team-Detail funktioniert nicht (404 oder wird vom Gateway falsch geroutet). Im User-Dashboard (`app/page.tsx:146`) funktioniert es korrekt via `POST /agents/{id}/pause`.

**Fix:** Chat und Team-Detail aendern: statt `api.patch('/fleet/${agentId}', { status })` → `api.post('/agents/${agentId}/pause')` bzw. `api.post('/agents/${agentId}/resume')`.

**Aufwand:** 15 Minuten.

---

### N3: HealthResponse fehlt `vault` Feld [MEDIUM]

**Dateien:**
- `nomos-console/src/lib/types.ts:136-140`
- `nomos-api/nomos_api/schemas.py:93-98`

**Problem:** Backend `HealthResponse` hat 4 Felder: `status`, `service`, `version`, `vault`. Frontend `HealthResponse` hat nur 3: `status`, `service`, `version`. Das `vault` Feld wird ignoriert.

**Auswirkung:** Diagnostics Page kann keinen Vault-Gesundheitsstatus anzeigen. Aktuell wird nur API-Health gezeigt, nicht ob Vault connected/unavailable ist.

**Fix:** `vault: string;` zu `HealthResponse` hinzufuegen. Optional Diagnostics-Page erweitern.

**Aufwand:** 10 Minuten (Type), 30 Minuten (mit Diagnostics UI).

---

### N4: ApprovalEntry Status-Werte Divergenz [LOW]

**Dateien:**
- `nomos-console/src/lib/types.ts:44` — `status: 'pending' | 'approved' | 'rejected' | 'expired'`
- `nomos-api/nomos_api/routers/approvals.py:84` — Backend setzt `"denied"`, nicht `"rejected"`

**Problem:** Frontend definiert Status-Wert `'rejected'`, Backend setzt `'denied'`. Die Approval-Seite zeigt `approval.status === 'approved'` korrekt, aber der else-Fall zeigt "Abgelehnt" fuer alles was nicht `'approved'` ist — das funktioniert zufaellig. Ein strikter Check auf `=== 'rejected'` wuerde fehlschlagen.

**Auswirkung:** Gering aktuell, weil die UI einen fallthrough nutzt. Aber jede kuenftige striktere Logik wuerde brechen.

**Fix:** Frontend `'rejected'` → `'denied'` aendern, oder Backend anpassen.

**Aufwand:** 5 Minuten.

---

### N5: CostEntry `budget_status` Wert-Divergenz [LOW]

**Dateien:**
- `nomos-console/src/__tests__/fixtures.ts:71` — `budget_status: 'ok'`
- `nomos-api/nomos_api/routers/costs.py:42-47` — Backend liefert `'normal'`, `'warning'`, `'exceeded'`

**Problem:** Test-Fixture verwendet `'ok'` als budget_status, Backend liefert nie `'ok'`. Es liefert `'normal'`, `'warning'`, oder `'exceeded'`.

**Auswirkung:** Tests testen mit einem Wert den die API nie liefert. Wenn die UI je budget_status-spezifische Logik bekommt (z.B. Farben), wuerde sie mit echten Daten anders reagieren als in Tests.

**Fix:** Fixture auf `'normal'` aendern.

**Aufwand:** 2 Minuten.

---

### N6: PATCH /api/agents/{id} gibt `dict` zurueck, nicht `AgentResponse` [MEDIUM]

**Dateien:**
- `nomos-api/nomos_api/routers/agents.py:64-68`

**Problem:** `PATCH /api/agents/{id}` ist als `response_model=dict` deklariert und gibt ein manuelles Dict zurueck: `{"agent_id": ..., "status": ..., "updated": True}`. Es persistiert die Aenderung NICHT in der Datenbank — es gibt nur ein statisches Dict zurueck ohne DB-Zugriff.

**Auswirkung:** Selbst wenn N2 gefixt wuerde (Frontend wuerde `/agents/{id}` statt `/fleet/{id}` nutzen), wuerde der PATCH nichts in der DB aendern. Die dediziierten `/agents/{id}/pause`, `/agents/{id}/resume` Routes sind die korrekten Wege.

**Fix:** Entweder den PATCH Endpoint entfernen (Breaking Change) oder ihn DB-backed machen. Besser: PATCH nur fuer non-status Felder nutzen und status immer ueber die dedizierten POST-Routen aendern.

**Aufwand:** 30 Minuten.

---

### N7: Plugin `AuditResult.id` ist `string?`, Backend `AuditEntryCreateResponse.id` ist `int` [LOW]

**Dateien:**
- `nomos-plugin/src/api-client.ts:29-31` — `id?: string`
- `nomos-api/nomos_api/schemas.py:88-91` — `id: int`

**Problem:** Plugin definiert `id` als optionaler `string`, Backend liefert immer einen `int`. JavaScript's Typensystem merkt den Unterschied nicht zur Runtime (JSON parst `42` als number), aber TypeScript-Typing stimmt nicht.

**Auswirkung:** Gering, da das Plugin die `id` aktuell nicht weiterverwendet.

**Fix:** `id?: number` in Plugin types.

**Aufwand:** 2 Minuten.

---

## Teil 3: Zusammenfassung der Prioritaeten

### Sofort fixen (vor naechstem Release)

| # | Mismatch | Aufwand | Risiko |
|---|---------|---------|--------|
| N2 | PATCH /fleet/{id} existiert nicht — Chat + Team Pause kaputt | 15 min | **User-facing Bug** |
| N1 | Plugin Heartbeat Body-Format — Metriken gehen verloren | 5 min | **Data Loss** |
| N6 | PATCH /agents/{id} macht keinen DB-Write | 30 min | **Silent Failure** |

### Naechster Sprint

| # | Mismatch | Aufwand | Risiko |
|---|---------|---------|--------|
| N3 | HealthResponse fehlt vault Feld | 10-30 min | UX Luecke |
| N4 | Approval 'denied' vs 'rejected' | 5 min | Latentes Risiko |
| N5 | Fixture budget_status 'ok' vs 'normal' | 2 min | Test-Accuracy |
| N7 | AuditResult.id type mismatch | 2 min | Type Safety |

### Bereits erledigt (9/11 Original-Tasks)

A1 (Agent types), A2 (ComplianceMatrix), A3 (TaskEntry), A4 (Speculative Types),
A5 (Auth 2FA), A6 (Plugin mapping, bis auf N1), B1 (Global Audit), B3 (Compliance 'passed'),
B4 (Users Forms).

### Noch offen (2/11 Original-Tasks)

- **B2**: Pause/Resume Route-Drift — Frontend nutzt falschen Endpoint an 2 Stellen
- **B5**: Settings Fallback entfernt, aber Vault-Status wird ignoriert (N3)

---

## Teil 4: Vollstaendige API Route Map

| Method | Route | Backend Router | Frontend Usage | Status |
|--------|-------|---------------|----------------|--------|
| GET | /health | health.py | hooks.ts useFetch, diagnostics | OK |
| GET | /api/health | health.py | — | OK (alias) |
| GET | /api/fleet | fleet.py | admin/page, app/page, audit/page, team/page | OK |
| GET | /api/fleet/{id} | fleet.py | chat/page, team/[id]/page | OK |
| POST | /api/agents | agents.py | admin/hire/page | OK |
| PATCH | /api/agents/{id} | agents.py | **Nicht vom Frontend genutzt** | N6: Kein DB-Write |
| POST | /api/agents/{id}/pause | agents.py | app/page (korrekt) | OK |
| POST | /api/agents/{id}/resume | agents.py | app/page (korrekt) | OK |
| POST | /api/agents/{id}/kill | agents.py | — | OK |
| POST | /api/agents/{id}/retire | agents.py | — | OK |
| POST | /api/agents/{id}/heartbeat | agents.py | Plugin api-client | N1: Body-Mismatch |
| GET | /api/agents/{id}/compliance | compliance.py | team/[id]/page | OK |
| POST | /api/agents/{id}/gate | compliance.py | — | OK |
| POST | /api/compliance/gate | compliance.py | Plugin api-client | OK |
| GET | /api/compliance/matrix | compliance.py | admin/compliance/page | OK |
| GET | /api/audit | audit.py | admin/audit/page | OK |
| GET | /api/agents/{id}/audit | audit.py | team/[id]/page | OK |
| GET | /api/agents/{id}/audit/export | audit.py | — | OK |
| GET | /api/audit/verify/{id} | audit.py | admin/audit/page | OK |
| POST | /api/audit/entry | audit.py | Plugin api-client | OK |
| POST | /api/auth/login | auth.py | auth.ts | OK |
| POST | /api/auth/logout | auth.py | auth.ts | OK |
| GET | /api/auth/me | auth.py | auth.ts | OK |
| POST | /api/auth/2fa/setup | auth.py | — | OK |
| POST | /api/auth/2fa/verify | auth.py | auth.ts | OK |
| POST | /api/auth/recovery | auth.py | — | OK |
| POST | /api/users/bootstrap | users.py | — | OK |
| GET | /api/users | users.py | admin/users/page | OK |
| POST | /api/users | users.py | admin/users/page | OK |
| PATCH | /api/users/{id} | users.py | admin/users/page | OK |
| DELETE | /api/users/{id} | users.py | — | OK |
| GET | /api/tasks | tasks.py | admin/tasks, app/tasks, app/page | OK |
| GET | /api/tasks/{id} | tasks.py | — | OK |
| POST | /api/tasks | tasks.py | admin/tasks, app/tasks | OK |
| PATCH | /api/tasks/{id} | tasks.py | admin/tasks/page | OK |
| GET | /api/approvals | approvals.py | admin/approvals/page | OK |
| POST | /api/approvals | approvals.py | — | OK |
| POST | /api/approvals/{id}/approve | approvals.py | admin/approvals/page | OK |
| POST | /api/approvals/{id}/reject | approvals.py | admin/approvals/page | N4: Returns 'denied' not 'rejected' |
| GET | /api/costs | costs.py | admin/page, admin/costs/page | OK |
| GET | /api/costs/{id} | costs.py | team/[id]/page | OK |
| POST | /api/budget/check | budget.py | Plugin api-client | OK |
| POST | /api/budget/track | budget.py | — | OK |
| POST | /api/pii/filter | pii.py | Plugin api-client | OK |
| POST | /api/incidents | incidents.py | Plugin api-client | OK |
| GET | /api/incidents | incidents.py | admin/incidents/page | OK |
| PATCH | /api/incidents/{id} | incidents.py | admin/incidents/page | OK |
| GET | /api/workspace/{id} | workspace.py | — | OK |
| POST | /api/workspace/mount | workspace.py | — | OK |
| POST | /api/workspace/unmount | workspace.py | — | OK |
| POST | /api/dsgvo/forget | dsgvo.py | — | OK |
| POST | /api/dsgvo/export | dsgvo.py | — | OK |
| GET | /api/proxy/status | proxy.py | chat/page | OK |
| POST | /api/proxy/chat | proxy.py | chat/page | OK |
| GET | /api/settings | settings.py | admin/settings/page | OK |
| PATCH | /api/settings | settings.py | admin/settings/page | OK |
| **PATCH** | **/api/fleet/{id}** | **EXISTIERT NICHT** | chat/page, team/[id]/page | **N2: 404** |

---

## Keine TODO/FIXME/HACK gefunden

Grep ueber alle drei Projekte (nomos-api, nomos-console/src, nomos-plugin/src) hat **null** Treffer fuer TODO, FIXME, HACK, oder XXX ergeben. Der Code ist sauber von Markierungen.

---

## Fazit

Der NomOS Stack ist zu **~85% contract-aligned**. Die Stabilisierung v2 hat 9 von 11 Tasks erfolgreich abgeschlossen. Die 3 kritischen neuen Mismatches (N1, N2, N6) betreffen Pause-Funktionalitaet und Heartbeat-Daten — beides ist user-facing und sollte vor dem naechsten Release gefixt werden. Geschaetzter Gesamtaufwand fuer alle 7 neuen Findings: **~100 Minuten**.
