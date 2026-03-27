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

## Aktiver Plan
- Stabilisierung v2: `docs/superpowers/plans/2026-03-27-stabilization-v2-plan.md`

## Sprache
- Code + Commits: Englisch
- Dokumentation: Bilingual DE/EN
- Kommunikation: Deutsch

## Commit Convention
`feat|fix|refactor|test|docs(component): description`
