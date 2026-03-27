# NomOS Stabilisierung — Contract Alignment, Console Truthfulness, Hygiene

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Frontend, Plugin und API auf identische Contracts bringen. Jede Console-Page zeigt nur was die API wirklich liefert. Repo aufraemen. Doku aktualisieren. Aus Fehlern lernen.

**Architecture:** `schemas.py` ist die EINZIGE Wahrheit. `types.ts` wird daraus abgeleitet. Jede Page die mehr zeigt als die API liefert wird zurueckgebaut. Kein Fake, kein Fallback auf erfundene Daten.

**Tech Stack:** Python 3.12 (FastAPI, Pydantic v2), TypeScript strict (Next.js 15), vitest

**Quelle:** Zwei unabhaengige Audits (full-spectrum + platform-drift) vom 27.03.2026

---

## Referenz-Dateien

| Datei | Rolle |
|---|---|
| `nomos-api/nomos_api/schemas.py` | **WAHRHEIT** — alle Response-Schemas |
| `nomos-console/src/lib/types.ts` | **CONSUMER** — muss schemas.py spiegeln |
| `nomos-plugin/src/api-client.ts` | **CONSUMER** — muss schemas.py spiegeln |
| `nomos-console/src/lib/auth.ts` | **CONSUMER** — Auth-Endpoints |
| `.gsd/audits/2026-03-27-*` | Audit-Reports mit allen Findings |

---

## TEIL A: Contract Alignment (S1 + S2 + S3)

### Task A1: types.ts — Agent + Fleet alignen

**Files:**
- Modify: `nomos-console/src/lib/types.ts`

**Mismatches:**
- `Agent` fehlt `heartbeat_at: string | null`
- `Agent.created_at/updated_at` sind `string` — korrekt, weil JSON serialisiert datetime als ISO string

- [ ] `Agent` Interface: `heartbeat_at: string | null` hinzufuegen
- [ ] `Agent.status`: `'retired'` hinzufuegen (existiert in API, fehlt im Union)
- [ ] Verifizieren: `tsc --noEmit` im `nomos-console/`
- [ ] Commit: `fix(types): Agent — add heartbeat_at, retired status`

---

### Task A2: types.ts — ComplianceMatrix alignen

**Files:**
- Modify: `nomos-console/src/lib/types.ts`
- Modify: `nomos-console/src/app/admin/compliance/page.tsx`

**Mismatch:** Frontend erfindet per-document Matrix, API liefert per-agent Summary.

Backend `ComplianceMatrixEntry`:
```python
agent_id: str, agent_name: str, status: str, missing_docs: list[str], risk_class: str
```

Frontend `ComplianceMatrixCell` erwartet:
```typescript
agent_id, agent_name, document_type, status: 'valid'|'expiring'|'missing', last_updated, expires_at
```

**Entscheidung:** Frontend an Backend anpassen. Die Compliance-Page zeigt pro Agent: Name, Status, fehlende Docs, Risk Class. Keine erfundene per-document Matrix.

- [ ] `ComplianceMatrixCell` ersetzen durch `ComplianceMatrixEntry` das Backend spiegelt:
```typescript
export interface ComplianceMatrixEntry {
  agent_id: string;
  agent_name: string;
  status: string;
  missing_docs: string[];
  risk_class: string;
}

export interface ComplianceMatrixResponse {
  matrix: ComplianceMatrixEntry[];
  total: number;
}
```
- [ ] `compliance/page.tsx` vereinfachen: Zeige Tabelle mit Agent | Status | Fehlende Docs | Risk Class
- [ ] Entferne die lokale Matrix-Transformation die Docs erfindet
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(compliance): align matrix with real API — no invented documents`

---

### Task A3: types.ts — Task alignen

**Files:**
- Modify: `nomos-console/src/lib/types.ts`
- Modify: `nomos-console/src/app/admin/tasks/page.tsx`
- Modify: `nomos-console/src/app/app/tasks/page.tsx`

**Mismatches:**
- `title` → existiert nicht, Backend hat `description`
- `agent_name` → existiert nicht im Backend
- `priority`: `medium/critical` → Backend hat `normal/urgent`
- `status`: fehlt `failed` im Frontend

- [ ] `TaskEntry` korrigieren:
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
- [ ] Tasks-Page: `title` durch `description` ersetzen, Priority-Labels anpassen
- [ ] Tasks-Page: Create-Form auf `description` + `agent_id` + `priority` reduzieren
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(tasks): align with real API — description not title, correct priority enum`

---

### Task A4: types.ts — Speculative Types entfernen

**Files:**
- Modify: `nomos-console/src/lib/types.ts`

**Problem:** Types die kein Backend-Pendant haben:
- `HeartbeatEntry` (kein Endpoint liefert dieses Format)
- `DailyCostEntry` / `CostDetailResponse` (API liefert nur `CostOverviewResponse`)
- `HealthStatus` (optional, API liefert es nicht)

- [ ] `HeartbeatEntry` entfernen (Diagnostics-Page nutzt Fleet-Daten stattdessen)
- [ ] `DailyCostEntry` / `CostDetailResponse` entfernen
- [ ] `HealthStatus` als optional markieren oder entfernen
- [ ] Alle Pages die diese Types importieren fixen
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(types): remove speculative types without backend support`

---

### Task A5: Auth 2FA Route + Response fixen

**Files:**
- Modify: `nomos-console/src/lib/auth.ts`
- Modify: `nomos-api/nomos_api/routers/auth.py`

**Mismatch:**
- Frontend: `POST /auth/totp/verify` → erwartet `{ user: MeResponse }`
- Backend: `POST /api/auth/2fa/verify` → gibt `{ verified: bool }`

**Entscheidung:** Backend erweitern — nach erfolgreicher TOTP-Verifizierung User-Daten mitliefern. Frontend-Route anpassen.

- [ ] Backend `auth.py`: Route `/api/auth/2fa/verify` → nach Verify den User zurueckgeben:
```python
return {"verified": True, "user": {"id": user.id, "email": user.email, "role": user.role, "name": ...}}
```
- [ ] Frontend `auth.ts`: Route von `/auth/totp/verify` auf `/auth/2fa/verify` aendern
- [ ] Test: `test_auth_router.py` — 2FA verify gibt User zurueck
- [ ] `tsc --noEmit` pass
- [ ] Commit: `fix(auth): align 2FA route name + response between frontend and backend`

---

### Task A6: Plugin api-client.ts alignen

**Files:**
- Modify: `nomos-plugin/src/api-client.ts`
- Modify: `nomos-plugin/src/hooks/before-agent-start.ts`
- Modify: `nomos-plugin/src/types.ts` (wenn noetig)
- Modify: `nomos-plugin/tests/` (betroffene Tests)

**Mismatches:**
1. `checkCompliance()` erwartet `{ passed, missing }` — API gibt `ComplianceResponse { status, missing_documents }`
2. `filterPII()` erwartet `{ filtered, found[] }` — API gibt `{ filtered, pii_count, matches[] }`
3. `checkBudget()` erwartet `{ allowed, remaining }` — API gibt dict mit mehr Feldern

- [ ] `checkCompliance()`: Response-Mapping anpassen (`status === 'passed'` → `passed: true`, `missing_documents` → `missing`)
- [ ] `filterPII()`: `found` → `matches` umbenennen, `pii_count` hinzufuegen
- [ ] `checkBudget()`: Response-Felder anpassen
- [ ] `before-agent-start.ts`: `result.passed` durch korrektes Feld ersetzen
- [ ] Plugin bauen: `cd nomos-plugin && npm run build`
- [ ] Plugin Tests: `cd nomos-plugin && npm test`
- [ ] Commit: `fix(plugin): align api-client with real backend response schemas`

---

## TEIL B: Console Truthfulness (S4)

### Task B1: Global Audit Endpoint + Page fixen

**Files:**
- Create: `nomos-api/nomos_api/routers/audit.py` (erweitern — globale Route)
- Modify: `nomos-console/src/app/admin/audit/page.tsx`

**Problem:** Page sagt selbst "Global /audit endpoint does not exist" und hardcoded empty.

- [ ] Backend: `GET /api/audit` Endpoint hinzufuegen der ALLE Audit-Entries aggregiert (mit Pagination)
- [ ] Page: Hardcoded empty entfernen, echten `useFetch('/audit')` nutzen
- [ ] Page: "Kette verifizieren" Button → echten `/api/audit/verify/{agent_id}` nutzen (pro Agent)
- [ ] Test: `test_audit.py` — globaler Endpoint
- [ ] Commit: `feat(audit): global audit endpoint + real verification in console`

---

### Task B2: Pause/Resume Route auf User-Dashboard fixen

**Files:**
- Modify: `nomos-console/src/app/app/page.tsx`

**Problem:** Page ruft `api.post('/agents/{id}/pause')` — korrekte Route ist `api.post('/fleet/{id}', {status: 'paused'})` oder direkt `/api/agents/{id}/pause`.

- [ ] Pruefen welche Route die API tatsaechlich hat (lies `routers/agents.py`)
- [ ] Page anpassen auf korrekte Route
- [ ] Commit: `fix(console): correct pause/resume route on user dashboard`

---

### Task B3: Compliance-Status Semantik alignen

**Files:**
- Modify: `nomos-console/src/app/admin/page.tsx`
- Modify: `nomos-console/src/app/admin/team/[id]/page.tsx`

**Problem:** Frontend prueft `compliance_status === 'compliant'`, Backend gibt `'passed'`.

- [ ] Alle Stellen finden: `grep -rn "compliant" nomos-console/src/`
- [ ] Ersetzen durch `'passed'` oder eine Helper-Funktion
- [ ] Commit: `fix(console): compliance_status 'passed' not 'compliant'`

---

### Task B4: Users Create/Edit Form alignen

**Files:**
- Modify: `nomos-console/src/app/admin/users/page.tsx`

**Problem:** Form sendet `name`, `max_tasks` — Backend `UserCreateRequest` akzeptiert nur `email`, `password`, `role`.

- [ ] Create-Form: nur `email`, `password`, `role` senden
- [ ] Edit-Form: nur `role`, `session_timeout_hours`, `is_active` senden
- [ ] `name`, `max_tasks` Felder entfernen oder als read-only anzeigen
- [ ] Commit: `fix(users): align create/edit forms with backend schema`

---

### Task B5: Settings-Page Read-Only Hinweis entfernen

**Files:**
- Modify: `nomos-console/src/app/admin/settings/page.tsx`

**Problem:** Page zeigt "Nur-Lese-Ansicht" obwohl API jetzt existiert.

- [ ] Hardcoded-Defaults Fallback entfernen (API existiert jetzt)
- [ ] "Nur-Lese-Ansicht" ist korrekt (wir haben kein PATCH), aber Wording klarstellen
- [ ] Commit: `fix(settings): remove hardcoded defaults, use real API data`

---

## TEIL C: Hygiene + Doku + Learnings (S5 + S6 + S7)

### Task C1: .gitignore + Repo aufraemen

**Files:**
- Modify: `.gitignore`
- Delete: tracked files die ignoriert sein sollten

- [ ] `.gitignore` ergaenzen:
```
# Claude Code / MCP / Tools
.claude/worktrees/
.bg-shell/
.gsd/
.playwright-mcp/

# Archive (historisch, nicht aktiv)
_archive/
```
- [ ] `git rm -r --cached _archive/` (aus Git entfernen, lokal behalten)
- [ ] `git rm --cached .claude/worktrees/agent-*`
- [ ] Commit: `chore: gitignore cleanup — remove archive, tool artifacts from tracking`

---

### Task C2: Dokumentation auf v2-Stand bringen

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/api-reference.md`

- [ ] README: Aktuelle Feature-Liste (8 Services, 13 Pages, 176 Tests)
- [ ] Architecture: Echte Architektur (Console → API → Gateway → LLM)
- [ ] API-Reference: Alle 17 Router mit echten Endpoints
- [ ] Feature Maturity Matrix: Was ist GA, was ist Beta, was fehlt
- [ ] Commit: `docs: refresh README, architecture, API reference to v2 reality`

---

### Task C3: CLAUDE.md + Learnings dokumentieren

**Files:**
- Modify: `.claude/CLAUDE.md`
- Create: `.claude/knowledge/LEARNINGS.md` oder in bestehendes einfuegen

**Learnings aus dieser Session:**

1. **Types von API ableiten, nicht erfinden** — Frontend-Types die nicht zur API passen crashen React
2. **Nicht raten, Doku lesen** — OpenClaw Endpoints, NVIDIA Model-Namen, Gateway Config
3. **Kein Feature auf Fake-Fundament** — 8 In-Memory Services haben alles instabil gemacht
4. **Ein Feld-Mismatch = ein Crash** — `payload.error` statt `payload.message`, `title` statt `description`
5. **Rate Limiter ist In-Memory** — bei API-Restart reset, bei zu vielen Tests lockt man sich selbst aus
6. **`is_active = false` unsichtbar** — User deaktiviert → Login 401 ohne klare Fehlermeldung
7. **Next.js rewrites sind Build-time** — `NOMOS_API_URL` muss beim Build gesetzt werden
8. **Windows Bind-Mounts = mode 777** — OpenClaw blockiert world-writable Plugins

- [ ] CLAUDE.md: Neue Rule `R13: Types von API ableiten`
- [ ] CLAUDE.md: Link zu Learnings
- [ ] Commit: `docs: CLAUDE.md learnings — types from API, no guessing, no fakes`

---

## Abhaengigkeiten

```
Teil A (Contracts):
  A1 (Agent) ──┐
  A2 (Matrix) ─┤── unabhaengig, parallel
  A3 (Tasks)  ─┤
  A4 (Speculative) ─── nach A1-A3 (entfernt was uebrig bleibt)
  A5 (Auth 2FA) ─── unabhaengig
  A6 (Plugin) ─── unabhaengig

Teil B (Console): nach Teil A
  B1 (Global Audit) ──┐
  B2 (Pause Route)  ──┤── unabhaengig, parallel
  B3 (Compliance)   ──┤
  B4 (Users Form)   ──┤
  B5 (Settings)     ──┘

Teil C (Hygiene): unabhaengig von A+B
  C1 (gitignore) ──┐
  C2 (Doku)      ──┤── parallel
  C3 (Learnings) ──┘
```

**Teil A1-A3 + A5-A6 parallel → A4 → Teil B parallel → Teil C parallel**
