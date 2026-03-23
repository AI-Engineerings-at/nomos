# NomOS — Development Rules

## Was ist NomOS?
NomOS (Nomos = Gesetz + OS) ist ein standalone Docker-Produkt das EU AI Act Compliance fuer AI-Agenten erzwingt. Kunden starten `docker compose up -d` auf IHREM Server.

## HARD RULES (gelten fuer ALLE Agents)

```
1. WEISST DU ES SICHER? Nein → LIES die Doku. Raten = VERBOTEN.
2. JOE HAT KORRIGIERT? STOPP. Plan neu. Joe vorlegen. ERST DANN weiter.
3. LANGSAM = GUT. Kein Output ohne Verstaendnis.
```

## S9 VERBOTEN (ohne Ausnahme)
1. **Quick-Fix** — Jeder Fix muss Root Cause adressieren.
2. **Mock-Daten** — Keine Fake-Metriken, keine Dummy-Responses.
3. **Platzhalter-Code** — Kein "TODO: implement later", kein "pass # placeholder".
4. **Fake-Visualisierungen** — Keine Dashboards mit erfundenen Daten.
5. **Skeleton-Dateien** — Keine Datei ohne echte Implementation + Test.

## Neue Regeln R8-R12

### R8: Scope Validation Gate (BLOCKER)
Vor JEDEM Code 3 Pflichtfragen beantworten:
1. Welches Problem loest dieser Code fuer den KUNDEN?
2. Kann ein Fremder das auf seinem Server deployen?
3. Gibt es einen Test der beweist dass es funktioniert?

### R9: Architecture Gate (GATE)
Kein Code ohne:
- User Story ("Als KMU-Chef will ich...")
- Interface-Definition (Inputs, Outputs, Fehler)
- Test-Strategie

### R10: Anti-Skeleton (BLOCKER)
Keine Datei wird committed die:
- "coming soon" enthaelt
- Eine leere Funktion hat (ausser abstrakte Interfaces)
- Einen "TODO" Kommentar hat
- Keinen zugehoerigen Test hat

### R11: Session-Limit (GATE)
- Max 1 Produkt-Komponente pro Session
- Review-Checkpoint nach jedem Task

### R12: Produkt/Infra Trennung (BLOCKER)
- KEINE internen IPs (10.40.10.x) in Produkt-Code
- KEINE Referenz zu .80, .82, .83, .90, .91, .99
- NomOS ist STANDALONE — laeuft auf dem Server des KUNDEN
- Interne Infra ist NUR die Dev-Umgebung

## Tech Stack
- Python 3.11+ (Backend: FastAPI, CLI: Click, Models: Pydantic v2)
- TypeScript strict (Console: Next.js 15, Plugin: OpenClaw)
- PostgreSQL + pgvector (Datenbank)
- Docker Compose (Deployment)
- pytest + ruff (Testing + Linting)
- GitHub Actions (CI/CD)

## Repo-Struktur (aktuell, nach Cleanup)
```
nomos/
├── nomos-cli/nomos/core/    # Manifest, Validator, HashChain, Events, Compliance, Forge
├── nomos-cli/tests/          # Tests fuer alles in core/
├── schemas/                  # YAML Schema Templates
├── templates/                # Agent Templates (external-secretary, etc.)
├── docs/plans/               # Implementation Plans (Plan 1-6)
└── .claude/agents/           # Dev-Team Agent Definitionen
```

## Sprache
- Code + Commits: Englisch
- Dokumentation: Bilingual DE/EN
- Kommunikation: Deutsch

## Commit Convention
`feat|fix|refactor|test|docs(component): description`
