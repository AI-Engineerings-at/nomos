# Session Report — Stabilisierung 27.03.2026

## Ziel
Alle Contract-Mismatches zwischen Frontend/Backend/Plugin beseitigen. Console-Pages auf Wahrheit zurueckbauen. Repo aufraumen. CI haerten. Doku aktualisieren.

## Ausgangslage
- 2 unabhaengige Audits identifizierten 25+ Mismatches
- types.ts erfand Felder die die API nicht liefert (title, agent_name, health_score, daily_trend)
- Compliance-Page zeigte eine 14-Dokument-Matrix die nicht existiert
- Audit-Page war hardcoded leer
- Settings-Page nutzte hardcoded Defaults trotz vorhandener API
- Plugin-Events wurden vom Backend abgelehnt (5 von 7 nicht registriert)
- Auth 2FA Route und Response-Format stimmten nicht ueberein
- CI liess Console-Fehler stillschweigend durch (continue-on-error)

## 15 Commits (fe33e0f → 1b42a56)

| # | Commit | Was |
|---|---|---|
| 1 | fe33e0f | types.ts: Agent + heartbeat_at + created/retired Status |
| 2 | 85e7871 | .gitignore: _archive, worktrees, .gsd, .bg-shell, .playwright-mcp |
| 3 | 51f110e | Auth 2FA: Route /auth/2fa/verify + User in Response |
| 4 | 4cb563b | Plugin: checkCompliance/filterPII Response-Mapping |
| 5 | 9377c85 | Events: 5 neue Plugin Event-Types registriert |
| 6 | 622032b | Compliance-Page: Erfundene 14-Doc Matrix → echte per-Agent Tabelle |
| 7 | ad72cac | Tasks: title→description, medium→normal, critical→urgent, +failed |
| 8 | 0ffc3ea | Speculative Types geloescht + Costs/Diagnostics Pages gefixt |
| 9 | a374ed4 | Global Audit Endpoint: GET /api/audit mit Pagination + Filter |
| 10 | 7f8354d | Console Truthfulness: Audit, Compliance Status, Users, Settings |
| 11 | 7aa8262 | CLAUDE.md: 9 Learnings dokumentiert |
| 12 | df1c079 | README, Architecture, API Reference auf v2 Stand |
| 13 | 6646048 | CI: continue-on-error entfernt, Summary gefixt |
| 14 | 65c4d45 | Stabilisierungsplan v2 dokumentiert |
| 15 | 1b42a56 | uv.lock Update |

## Was vorher war → Was jetzt ist

| Vorher | Nachher |
|---|---|
| Agent.status: 5 Werte, kein heartbeat_at | 7 Werte (+ created, retired), heartbeat_at |
| ComplianceMatrix: 14 erfundene Dokumente | Per-Agent Summary (status, missing_docs, risk_class) |
| Task: title + medium/critical | description + normal/urgent + failed |
| Auth 2FA: /auth/totp/verify → 404 | /auth/2fa/verify → { verified, user } |
| Plugin: falsche Response-Felder | Korrektes Mapping (status→passed, missing_documents→missing) |
| 5 Plugin-Events rejected | Alle 7 Events registriert in EventType Enum |
| Audit-Page: hardcoded leer | Echte Daten via GET /api/audit |
| Dashboard Activity: hardcoded leer | Echte Daten via /api/audit?limit=10 |
| Compliance Status: 'compliant' (falsch) | 'passed' (korrekt, 3 Stellen gefixt) |
| Users Form: name + max_tasks (ungueltig) | email + password + role (Create), role + timeout + active (Edit) |
| Settings: hardcoded Defaults | useFetch('/settings') mit Error-State |
| Costs: CostDetailResponse + daily_trend | CostOverviewResponse (was die API wirklich liefert) |
| Diagnostics: HealthStatus[] + uptime | Einfaches {status, service, version} |
| CostDetailResponse, HeartbeatEntry, etc. | Geloescht (4 speculative Interfaces) |
| CI: continue-on-error auf Console | Console-Fehler brechen Pipeline ab |
| .gitignore: fehlte _archive, worktrees | Alle Tool-Artefakte ignoriert |
| README: 7 Endpoints, 97 Tests | 47+ Endpoints, 770+ Tests, 20 Pages |
| API-Reference: 8 Endpoints | Alle 47+ Endpoints dokumentiert |

## Metriken

- **14 Tasks** in 4 Phasen ausgefuehrt
- **15 Commits**, alle auf main
- **25+ Mismatches behoben** (types.ts, auth.ts, api-client.ts, events.py)
- **~800 Zeilen geloescht** (erfundene Matrix, speculative Types, hardcoded Defaults, fake Verifikation)
- **~400 Zeilen hinzugefuegt** (echte API-Calls, korrigierte Types, neue Tests, Doku)
- **Netto: -400 Zeilen** (weniger Code, mehr Wahrheit)

## Methodik

1. **Analyse**: 4 parallele Agenten analysierten Backend/Frontend/Plugin/Repo
2. **Plan**: Umfassender Plan mit Mismatch-Matrix, exaktem Code, Phasen-Abhaengigkeiten
3. **Review**: Plan-Review durch Code-Reviewer Agent → 6 Findings gefixt
4. **Ausfuehrung**: Subagent-Driven Development — 1 Agent pro Task, serialisiert auf types.ts
5. **Phase 1**: A1-A3 (Types) + A5 (Auth) + A6 (Plugin) + A7 (Events) + C1 (Gitignore)
6. **Phase 2**: A4 (Speculative Types + Costs + Diagnostics)
7. **Phase 3**: B1-B4 (Audit, Compliance Status, Users, Settings)
8. **Phase 4**: C2-C4 (CI, Doku, Learnings)

## 9 Learnings

1. **Types von API ableiten, nicht erfinden** — Frontend-Types die nicht zur API passen crashen React
2. **Nicht raten, Doku lesen** — OpenClaw Endpoints, NVIDIA Model-Namen, Gateway Config
3. **Kein Feature auf Fake-Fundament** — 8 In-Memory Services haben alles instabil gemacht
4. **Ein Feld-Mismatch = ein Crash** — `title` statt `description`, `compliant` statt `passed`
5. **Rate Limiter ist In-Memory** — bei API-Restart reset, bei zu vielen Tests lockt man sich selbst aus
6. **`is_active = false` unsichtbar** — User deaktiviert → Login 401 ohne klare Fehlermeldung
7. **Next.js rewrites sind Build-time** — `NOMOS_API_URL` muss beim Build gesetzt werden
8. **Windows Bind-Mounts = mode 777** — OpenClaw blockiert world-writable Plugins
9. **Plugin Event-Types muessen registriert sein** — audit.py validiert, unbekannte Events werden abgelehnt

## Bekannte offene Punkte

| Prio | Was | Status |
|---|---|---|
| 1 | **Settings-Page editierbar** — Kunde gibt LLM API Key ein | Nicht gestartet |
| 2 | **Budget-Hook undefined** — Agent "default" hat kein Budget | Plugin-Fix noetig |
| 3 | **Console Tests** — vitest fuer 20 Pages | Nicht gestartet |
| 4 | **E2E Integration Tests** — Login → Agent → Chat → Audit | Nicht gestartet |
| 5 | **Contract-Test in CI** — schemas.py vs types.ts automatisch pruefen | Nicht gestartet |

## PDCA-Audit

> "Kann ein Kunde docker compose up machen, sich einloggen, einen Agent einstellen, und mit ihm chatten?"

| Schritt | Status |
|---|---|
| docker compose up | **JA** — 5 Services healthy |
| Login | **JA** — JWT Cookie, 2FA aligned |
| Agent sehen | **JA** — Dashboard, Team, Hire |
| Chat oeffnen | **JA** — Art.14 Pause, Art.50 Label |
| LLM antwortet | **JA** — via OpenClaw Gateway |
| Console zeigt echte Daten | **JA** — alle Pages auf API aligned |
| Audit funktioniert | **JA** — globaler Endpoint, echte Verifikation |
| Plugin Events werden gespeichert | **JA** — alle 7 Event-Types registriert |
