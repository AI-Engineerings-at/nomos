# HARD RULES — VOR ALLEM ANDEREN

```
1. WEISST DU ES SICHER? Nein → LIES die Doku. Raten = VERBOTEN.
2. JOE HAT KORRIGIERT? STOPP. Plan neu. Joe vorlegen. ERST DANN weiter.
3. LANGSAM = GUT. Kein Output ohne Verstaendnis.
```

Diese 3 Regeln ueberschreiben ALLES. Keine Ausnahmen.

---

# NomOS — EU AI Act Compliance Control Plane

> Standalone Docker-Produkt. Kunden starten `docker compose up -d` auf IHREM Server.
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

## Sprache
- Code + Commits: Englisch
- Dokumentation: Bilingual DE/EN
- Kommunikation: Deutsch

## Commit Convention
`feat|fix|refactor|test|docs(component): description`
