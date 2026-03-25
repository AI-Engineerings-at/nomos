# NomOS Roadmap — KORRIGIERT 24.03.2026

> Stand: 24.03.2026
> WARNUNG: Plan 1-8 haben eine Library + UI gebaut, NICHT das Produkt.
> Die richtige Reihenfolge beginnt bei NemoClaw + Agent Deploy.
> Alles davor ist Vorarbeit (Library), nicht Produkt.

## EHRLICHER STAND (24.03.2026)

**Was existiert:** Core Library (84 Tests), API (19 Tests), Console (rendert), Plugin (kompiliert)
**Was FEHLT:** NemoClaw Container, Agent Deploy, Governance Runtime, Kill Switch, PII-Filter, Branding
**Bewertung:** 1/10 vom Produkt. Library funktioniert, Produkt existiert nicht.

---

## Warum 7 Plaene statt 1?

NomOS hat 7 unabhaengige Subsysteme. Ein Senior Dev baut nicht alles parallel,
sondern Schicht fuer Schicht — jede getestet bevor die naechste beginnt.

---

## Plan-Uebersicht

| Plan | Was | Abhaengig von | Agents |
|------|-----|---------------|--------|
| **1** | Cleanup + Foundation | — | backend, qa, security |
| **2** | NomOS API | Plan 1 | + architect, devops |
| **3** | NomOS Compliance Gate | Plan 1 | + compliance |
| **4** | nomos-cli | Plan 1 + 2 | backend, qa |
| **5** | NomOS Console | Plan 2 | + frontend |
| **6** | NomOS Plugin | Plan 1 | + architect |
| **7** | Production-Ready Stack | Plan 1+2 | devops |

---

## Plan 1: Cleanup + Foundation (AKTUELL)

**Status:** Plan geschrieben, Review abgeschlossen, 9 Issues gefixt.
**Datei:** `docs/plans/2026-03-23-plan-01-cleanup-foundation.md`

**Was passiert:**
1. Alle S9-Skeletons entfernen (nomos-api, nomos-gate, nomos-console, cli.py)
2. CI fixen (nur was existiert testen)
3. `hash_chain.py` — Tamper-evident Audit Trail (11 Tests)
4. `events.py` — Event Types Contract (7 Tests)
5. `compliance_engine.py` — Blocking Gate (7 Tests)
6. `forge.py` — Agent-Erstellung aus Name+Role (9 Tests)

**Ergebnis:** 55 Tests, 0 Skeletons, CI gruen, Core-Library komplett.

---

## Plan 2: NomOS API (NAECHSTER)

**Voraussetzung:** Plan 1 komplett + gruen.

**Was passiert:**
- OpenAPI Spec ZUERST (Architect designt)
- PostgreSQL Schema (SQLAlchemy Models)
- FastAPI Endpoints: /fleet, /agents, /compliance, /audit
- Health Check + Graceful Shutdown
- Integration Tests gegen echte DB
- Docker Compose (nur API + Postgres + Redis)

**Ergebnis:** Funktionierendes API das Fleet Registry, Compliance Status und Audit Trail liefert.

---

## Plan 3: NomOS Compliance Gate

**Voraussetzung:** Plan 1 komplett.

**Was passiert:**
- AALF Engine integrieren (existierende 10 Templates)
- Streamlit 8-Step Wizard
- Manifest-driven: liest Agent-Manifest, prueft was fehlt
- BLOCKING: Agent startet NICHT ohne signierte Docs
- PDF-Generierung fuer Compliance-Dokumente

**Ergebnis:** `nomos hire` fuehrt durch 8 Steps → 10 Compliance-Dokumente generiert + signiert.

---

## Plan 4: nomos-cli

**Voraussetzung:** Plan 1 + 2 komplett.

**Was passiert:**
- Click CLI Framework
- `nomos hire` — Forge + Compliance Gate + Deploy
- `nomos deploy` — Docker Container starten
- `nomos verify` — Compliance Check
- `nomos fleet` — Status aller Agents
- `nomos audit` — Audit Trail exportieren
- `nomos retire` — Agent dekommissionieren

**Ergebnis:** Vollstaendiger Agent Lifecycle ueber CLI.

---

## Plan 5: NomOS Console

**Voraussetzung:** Plan 2 komplett (API muss laufen).

**Was passiert:**
- Next.js 15 + TypeScript strict + Tailwind
- /fleet — Agent-Uebersicht
- /agent/[id] — Detail mit Compliance, Audit, Kosten
- /compliance — Matrix (Agents x Gesetze)
- /audit — Audit Trail Viewer
- "Mitarbeiter einstellen" Button → Compliance Gate
- Bilingual (DE + EN)

**Ergebnis:** Dashboard fuer KMU-Geschaeftsfuehrer.

---

## Plan 6: NomOS Plugin

**Voraussetzung:** Plan 1 komplett.

**Was passiert:**
- TypeScript OpenClaw Plugin (wie NemoClaw)
- Registriert sich bei Gateway-Start mit Banner
- `openclaw nomos status/verify/hire/audit` Commands
- Governance Hooks (pre-message, post-message, compliance-gate)
- v3 Python Hooks → TypeScript portieren

**Ergebnis:** NomOS integriert sich nativ in OpenClaw Gateway.

---

## Plan 7: Production-Ready Stack (DONE)

**Status:** Abgeschlossen
**Datei:** `docs/plans/2026-03-23-plan-07-production-ready.md`

**Was passiert:**
1. Master docker-compose.yml am Repo-Root
2. Dockerfiles gefixt (non-root, curl, standalone)
3. E2E Test Script (scripts/e2e-test.sh)
4. .dockerignore
5. CI Docker-Build Job

**Ergebnis:** `docker compose up -d` startet den kompletten Stack.

---

## Was NICHT im Scope ist

- Mani Phase 2 (Social Media) — eigener Scope
- Website Rework — eigener Scope
- Branding v2 — eigener Scope
- NemoClaw-spezifische Features — zu jung
- Cloud Hosting Setup — erst nach funktionierendem Produkt

---

## Entscheidungen die gefallen sind

1. **Senior Dev Approach**: Bottom-up, Schicht fuer Schicht, TDD
2. **S9 Enforcement**: Keine Skeletons, kein "coming soon"
3. **R8-R12**: Neue Regeln aus der Session-Analyse
4. **Agent-Team**: 4 Agents jetzt, weitere bei Bedarf (YAGNI)
5. **Plan-Reihenfolge**: 1→2→3→4→5→6 (Abhaengigkeitskette)
6. **Qualitaet > Geschwindigkeit**: Kein "kuerzester Weg"

---

## Analyse-Ergebnisse (in open-notebook, Notebook: NemoClaw OpenClaw Ecosystem)

| Source | Titel |
|--------|-------|
| source:oem41k91m1zgu5neh1ga | Session-Analyse: Was lief falsch |
| source:yl0x7sp3pck0k9shrjvc | NomOS SOLL vs IST vs Vision |
| source:xryuplrrhn71sclox921 | Root Cause: WARUM nicht umgesetzt |
| source:yqdtfka76oace07h0kn7 | Joes Kommunikation + Verbesserungen |
| source:cctah9txxs00gs51frra | Session-Struktur + Scope Creep |
| source:ekf9g8hpger65koomo7b | Ehrliche Inventur |
| source:typufsallrz40bvn6bka | Claudes Verhaltensmuster |
| source:rmxf7q6lwnexm2ez0xb1 | Lessons Learned + R8-R12 |
| source:yow77ah75gzigrat7420 | GAP-Analyse Vision vs Realitaet |
| source:5cgb728tolmyq6xoxtdc | GOTCHA: Claudes ehrliche Sicht |

---

## ERPNext

- EPIC: TASK-2026-00340 — NomOS
- Phase 0: TASK-00341, 00342, 00343
- Phase 1-5: TASK-00344 bis TASK-00356
