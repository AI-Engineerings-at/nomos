# HARD RULES — VOR ALLEM ANDEREN

```
1. WEISST DU ES SICHER? Nein → LIES die Doku. Raten = VERBOTEN.
2. JOE HAT KORRIGIERT? STOPP. Plan neu. Joe vorlegen. ERST DANN weiter.
3. LANGSAM = GUT. Kein Output ohne Verstaendnis.
```

Diese 3 Regeln ueberschreiben ALLES. Keine Ausnahmen.

---

# NomOS — EU AI Act Compliance Control Plane

> Enterprise Docker-Produkt mit 3 Deployment-Tiers: Enterprise VPS (managed), Docker Self-Hosted, Open-Source.
> Kunden starten `docker compose up -d` auf ihrem Server. Secret Management via HashiCorp Vault.
> LLM-provider-agnostic. FCL: 3 Agents gratis, ab 4 kommerziell.
> Leitsatz: *"Jeder entwickelt fuer sich, wir fuer alle."*

## Universelle Rules
- **Safety S1-S10**: siehe `phantom-ai/.claude/rules/01-safety-rules.md`
- **Firma-Regeln**: siehe `Playbook01/.claude/CLAUDE.md`
- **Fehler + Muster**: siehe `phantom-ai/.claude/knowledge/ERRORS.md` + `LEARNINGS.md`

## Tech Stack
- Python 3.12 (FastAPI, Click, Pydantic v2, pytest, ruff)
- TypeScript strict (Next.js 15, OpenClaw Plugin SDK, vitest, Playwright)
- PostgreSQL + pgvector, Valkey (BSD-3 Redis Replacement)
- Piper TTS (MIT) + Whisper.cpp (MIT) — optional
- Docker Compose (Deployment), GitHub Actions (CI/CD)

## NomOS-spezifische Rules (.claude/rules/)
- `01-produkt-standalone.md` — Produkt/Infra Trennung, keine internen IPs
- `02-integration-first.md` — Stack zuerst, Mocks verboten, Types von API ableiten
- `03-agent-fuehrung.md` — Plan lesen, Self-Check, GAP melden
- `04-pdca-zyklus.md` — Post-Phase Pruefung, Korrektur, Rescope

## Wo finde ich was
| Thema | Pfad |
|-------|------|
| Design Spec | `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` |
| Master Plan | `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md` |
| OpenClaw/NemoClaw Referenz | `docs/references/openclaw-nemoclaw-reference.md` |
| Postmortem | `docs/reports/2026-03-25-session-postmortem.md` |
| Sub-Plaene | `docs/superpowers/plans/2026-03-25-sub-*.md` |

## Learnings (27-28.03.2026)

### Session 27.03 (Stabilisierung v2)
1. **Types von API ableiten, nicht erfinden** — Frontend-Types die nicht zur API passen crashen React
2. **Nicht raten, Doku lesen** — OpenClaw Endpoints, NVIDIA Model-Namen, Gateway Config
3. **Kein Feature auf Fake-Fundament** — 8 In-Memory Services haben alles instabil gemacht
4. **Ein Feld-Mismatch = ein Crash** — `title` statt `description`, `compliant` statt `passed`
5. **Rate Limiter ist Distributed** — Valkey-backed, persistiert bei API-Restart
6. **`is_active = false` unsichtbar** — User deaktiviert → Login 401 ohne klare Fehlermeldung
7. **Next.js rewrites sind Build-time** — `NOMOS_API_URL` muss beim Build gesetzt werden
8. **Windows Bind-Mounts = mode 777** — OpenClaw blockiert world-writable Plugins
9. **Plugin Event-Types muessen registriert sein** — audit.py validiert, unbekannte Events werden abgelehnt

### Session 28.03 (Phase 2.1 Vitest + NSS Discovery)
10. **Compliance ist Architektur, nicht Feature** — NomOS ist eine "Compliance Control Plane" (Design Spec), aber Phase 2.1 testete nur UI. Guardian Shield (MARS, SENTINEL, APEX, SHIELD, VIGIL), EU AI Act, GDPR sind nicht optional, sind das Produkt.
11. **Test Factory Pattern skaliert** — 4-state coverage factory reduzierte boilerplate von 100+ auf 13 Zeilen pro Page-Test. Einfache Patterns sind mächtig.
12. **Fixtures als Kontrakt** — Mock-Daten die API-Schemas matchen verhindern zukünftige Type Mismatches. Fixtures sind erste Linie der Defense.
13. **Security Audit Early** — NVIDIA_API_KEY in `.env` (local, gitignored, aber real). Rotation jetzt ist besser als später.
14. **Plan vs. Product Spec Mismatch** — Plan sagte "Control Plane" aber Tests waren "UI Panel". Align Testplan mit Product-Definition von Anfang an.

### Session 01.04 (Leak-Analyse + OpenClaw Update + Full Audit)
15. **Claude Code Leak: 90% irrelevant fuer NomOS** — Unterschiedliche Produktkategorie (CLI Agent vs. Control Plane). Nuetzlich: Schema-first bestaetigt, Hook-Blaupause (155 Files)
16. **OpenClaw Releases pruefen BEVOR man weiterbaut** — v2026.3.22 hatte 13 Breaking Changes, unser Plugin Entry Point war veraltet. Immer Image pinnen, nie `latest`.
17. **definePluginEntry() ist Pflicht seit v2026.3.22** — Altes `export default function register()` wird deprecated
18. **Projekt Genesis: Nur paths-Frontmatter ist sinnvoll** — Worktree-Script, Coordinator, Scratchpad, Microcompaction sind bereits in Claude Code eingebaut
19. **NACH JEDEM RENAME: grep nach dem alten Namen** — `newStatus` → `action` Rename in team/[id] liess eine Referenz stehen → ReferenceError. IMMER `grep -r "alteName"` nach jedem Rename.
20. **NACH JEDER TYPE-AENDERUNG: alle Fixtures/Mocks pruefen** — `vault` Feld zu HealthResponse hinzugefuegt aber mockHealth Fixture vergessen. IMMER `grep -r "TypeName"` und alle Instanzen aktualisieren.
21. **NACH JEDEM FIX: alle Tests laufen lassen SOFORT** — Nicht erst am Ende. Jeder einzelne Fix → Test Run. Haette test_health Drift sofort aufgedeckt.
22. **Kleine Gaps = grosse Fehler** — Ein vergessenes Rename, eine vergessene Fixture, ein fehlender Guard — jedes davon ist ein Runtime-Crash fuer den Kunden. Null Toleranz.

## Aktiver Plan
- Enterprise Hardening Phase 0-2: COMPLETE
- OpenClaw v2026.3.28 Kompatibilitaet: DONE — TASK-2026-00529
- Contract-Alignment: DONE (9 Fixes) — TASK-2026-00535
- Alembic DB-Migrationen: DONE — TASK-2026-00542
- Full Audit P0 Fixes: DONE (API-Key Header, Test Count, Broken Tests)
- TASK-00545: Auth auf State-Change Endpoints: DONE (RBAC, 15 Tests)
- TASK-00546: Compliance-Dokumente 5→14: DONE (20 Tests, risikoklassenabhaengig)
- TASK-00544: Background Worker ARQ: DONE (4 Cron-Jobs, 9 Tests)
- TASK-00543: TLS via Caddy: DONE (Reverse Proxy, Cookie Hardening, 3 Tests)
- **Production Readiness: ~8/10** (war 5/10)
- **Naechste Schritte:** Final Validation, Docker Stack E2E Test, Deployment Guide

## OpenClaw Versionsstand (01.04.2026)
- **Gepinnt auf:** v2026.3.28 (Dockerfile.gateway)
- **Entry Point:** `definePluginEntry()` (v2026.3.22+ Pattern)
- **Neue Features verfuegbar:** `requireApproval`, `prependSystemContext`, ContextEngine Plugin Slot
- **NemoClaw:** Alpha, optional, kein Handlungsbedarf

## Sprache
- Code + Commits: Englisch
- Dokumentation: Bilingual DE/EN
- Kommunikation: Deutsch

## Commit Convention
`feat|fix|refactor|test|docs(component): description`
