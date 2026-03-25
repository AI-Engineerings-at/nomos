# NomOS — Development Rules

## Was ist NomOS?
NomOS (Nomos = Gesetz + OS) ist ein standalone Docker-Produkt das EU AI Act Compliance fuer AI-Agenten erzwingt. Kunden starten `docker compose up -d` auf IHREM Server. NomOS ist LLM-provider-agnostic — der Kunde waehlt seinen Anbieter, NomOS dokumentiert und erzwingt die passende Compliance.

**Leitsatz:** *"Jeder entwickelt fuer sich, wir fuer alle."*

**Lizenz:** FCL (Fair Core License) — 3 Agents gratis mit vollem Funktionsumfang, ab 4 kommerziell.

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

## Regeln R8-R12

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
- Python 3.12 (Backend: FastAPI, CLI: Click, Models: Pydantic v2)
- TypeScript strict (Console: Next.js 15, Plugin: OpenClaw)
- PostgreSQL + pgvector (Datenbank)
- Valkey (Event Bus, Queue) — BSD-3, Drop-in Redis Replacement
- Piper TTS (MIT) + Whisper.cpp (MIT) — optionale lokale Sprach-Services
- Docker Compose (Deployment)
- pytest + ruff (Testing + Linting)
- GitHub Actions (CI/CD)

## Repo-Struktur (Stand: 25.03.2026)
```
nomos/
├── nomos-cli/nomos/core/    # manifest, validator, hash_chain, events, compliance, gate, forge
├── nomos-cli/nomos/cli.py   # CLI: hire, verify, fleet, audit, gate
├── nomos-cli/tests/          # 84 Tests
├── nomos-api/nomos_api/     # FastAPI: config, database, models, schemas, services, routers
├── nomos-api/tests/          # 14 Tests
├── templates/                # Agent Templates (Mani, Rico)
├── scripts/e2e-test.sh       # E2E Test Script
├── docker-compose.yml        # Master Stack
├── docs/
│   ├── superpowers/specs/    # Design Spec v4
│   ├── superpowers/plans/    # Master Plan + Sub-Projekt Plaene
│   ├── reviews/              # Externes Feedback
│   ├── de/                   # Deutsche Doku
│   └── *.md                  # Englische Doku
├── _archive/                 # Archivierte v1-Komponenten
│   ├── console-v1/           # Altes Next.js Dashboard (wird neu gebaut)
│   ├── plugin-v1/            # Altes OpenClaw Plugin (wird neu gebaut)
│   ├── schemas-v1/           # Alte YAML Schemas
│   └── plans-v1/             # Alte Implementation Plans
└── .claude/                  # Dev-Regeln + Agent-Definitionen
```

## Implementation Plan
- **Master Plan:** `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md`
- **Design Spec:** `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` (v4)
- **6 Phasen, 9 Sub-Projekte (A-I)**
- **Naechste Phase:** 0 (Repo-Reorg) → dann Phase 1 (Plugin Core + Auth)

## Sprache
- Code + Commits: Englisch
- Dokumentation: Bilingual DE/EN
- Kommunikation: Deutsch

## Commit Convention
`feat|fix|refactor|test|docs(component): description`
