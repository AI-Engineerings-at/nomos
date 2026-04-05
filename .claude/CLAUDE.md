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

## Learnings
28 Erkenntnisse dokumentiert in `.claude/knowledge/LEARNINGS.md` (L001-L028).
Die wichtigsten 3:
- **L023:** Unit Tests ersetzen keinen Browser-Test. IMMER docker compose up + Browser.
- **L025:** Hardcoded Listen im Frontend sind Gift. IMMER vom Backend laden.
- **L026:** Onboarding muss Zero-Friction sein. Compliance-Docs automatisch generieren.

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
- TASK-00556: Hire-to-Chat Flow: DONE (Auto-Generate Docs, Auto Kill Switch, Compliance Banner)
- Integration Test: 8/8 Docker Services healthy, Hire→Compliant funktioniert
- Chat: Architektonisch funktioniert, NVIDIA Rate Limit blockiert (429)
- **Production Readiness: 8/10**
- **Naechste Session:** Chat E2E mit alternativem Provider, Umlaut-Fix, Deployment Guide

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
