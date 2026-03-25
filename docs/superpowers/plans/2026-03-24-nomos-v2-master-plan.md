# NomOS v2 — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **WICHTIG:** Jedes Sub-Projekt (A–I) bekommt seinen EIGENEN detaillierten TDD-Plan als separates Dokument. Dieser Master-Plan definiert Phasen, Abhaengigkeiten, Dateistruktur und Scope pro Sub-Projekt.

**Goal:** NomOS v1 (CLI-Tool mit 84 Tests) in ein produktionsreifes Compliance Control Plane Produkt transformieren das EU AI Act und DSGVO Konformitaet fuer OpenClaw/NemoClaw erzwingt.

**Architecture:** NomOS ist ein OpenClaw Plugin (TypeScript) das sich in den Gateway einklinkt und 11 Runtime Hooks ausfuehrt. Dahinter steht eine FastAPI (Python) als Control Plane mit PostgreSQL/pgvector + Valkey. Die Console (Next.js 15) ist der EINZIGE Zugang fuer den Kunden. NomOS ist LLM-provider-agnostic — der Kunde waehlt seinen Anbieter, NomOS dokumentiert und erzwingt die passende Compliance. Alles laeuft in Docker Compose auf dem Server des Kunden.

**Leitsatz:** *"Jeder entwickelt fuer sich, wir fuer alle."*

**Tech Stack:**
- Python 3.12 (FastAPI, Pydantic v2, Click, pytest, ruff)
- TypeScript strict (Next.js 15, OpenClaw Plugin SDK, vitest, Playwright)
- PostgreSQL + pgvector (Fleet Registry, Audit Trail, Honcho Storage)
- Valkey (Event Bus, Honcho Queue) — BSD-3, Drop-in Redis Replacement
- Piper TTS (MIT) + Whisper.cpp (MIT) — optionale lokale Sprach-Services
- Lizenz: FCL (Fair Core License) — 3 Agents gratis, voller Funktionsumfang
- Docker Compose (Deployment)
- GitHub Actions (CI/CD)

**Design Spec:** `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` (v3)

**Brand Bible:** `Playbook01/docs/BRAND-BIBLE-V2.md` — Company Soul, 6 Pflicht-Mehrwerte, Dual-Layer, Enterprise-Saeulen

---

## Regeln die fuer JEDEN Sub-Plan gelten

### Aus CLAUDE.md (BLOCKER — kein Code ohne das)

```
R8:  Scope Validation Gate — 3 Fragen VOR jedem Code:
     1. Welches Problem loest dieser Code fuer den KUNDEN?
     2. Kann ein Fremder das auf seinem Server deployen?
     3. Gibt es einen Test der beweist dass es funktioniert?

R9:  Architecture Gate — Kein Code ohne:
     - User Story ("Als KMU-Chef will ich...")
     - Interface-Definition (Inputs, Outputs, Fehler)
     - Test-Strategie

R10: Anti-Skeleton (BLOCKER) — Keine Datei die:
     - "coming soon" / "TODO" / "pass # placeholder" enthaelt
     - Eine leere Funktion hat (ausser abstrakte Interfaces)
     - Keinen zugehoerigen Test hat

R11: Session-Limit — Max 1 Produkt-Komponente pro Session

R12: Produkt/Infra Trennung (BLOCKER):
     - KEINE internen IPs (10.40.10.x) in Produkt-Code
     - NomOS ist STANDALONE — laeuft auf dem Server des KUNDEN
```

### Aus Brand Bible (PFLICHT fuer jede Komponente)

```
Company Soul — 6 Pflicht-Mehrwerte:
  1. Enterprise-Architektur (Fallbacks, Error Handling, Retry)
  2. Anleitung direkt im Produkt (Inline-Hilfe, Tooltips)
  3. HW/Budget Empfehlungen
  4. Top-5 Fehlerbehebung eingebaut
  5. Bilingual DE + EN
  6. Sofort lauffaehig nach docker compose up

Enterprise-Saeulen (PFLICHT fuer technische Komponenten):
  A. Global Error Handler
  B. State Management & Idempotenz
  C. Sub-Workflow Architektur (modulare Bloecke)

Dual-Layer:
  Easy Layer: KMU-Chef versteht es in 15 Minuten
  Deep Layer: Techniker findet Architektur-Erklaerungen
```

### S9 VERBOTEN (ohne Ausnahme)

```
1. Kein Quick-Fix — Root Cause adressieren
2. Keine Mock-Daten — Keine Fake-Metriken
3. Kein Platzhalter-Code — Kein "TODO: implement later"
4. Keine Fake-Visualisierungen — Dashboards zeigen echte Daten
5. Keine Skeleton-Dateien — Keine Datei ohne echte Implementation + Test
```

---

## Bestandsaufnahme: Was existiert (v1)

| Modul | Zeilen | Tests | Status | Aktion in v2 |
|-------|--------|-------|--------|-------------|
| `nomos-cli/nomos/core/manifest.py` | 225 | 21 | REAL | Erweitern (Budget, Approval, Memory Config) |
| `nomos-cli/nomos/core/gate.py` | 332 | 12 | REAL | Erweitern (5→14 Dokumente) |
| `nomos-cli/nomos/core/hash_chain.py` | 189 | 12 | REAL | Behalten |
| `nomos-cli/nomos/core/forge.py` | 164 | 9 | REAL | Erweitern (Forge v2: Budget, Approval, Memory) |
| `nomos-cli/nomos/core/compliance_engine.py` | 102 | 10 | REAL | Behalten |
| `nomos-cli/nomos/core/manifest_validator.py` | 76 | 21 | REAL | Behalten |
| `nomos-cli/nomos/core/events.py` | 68 | 9 | REAL | Erweitern (+10 Event Types) |
| `nomos-cli/nomos/core/cli.py` | 269 | — | REAL | Erweitern (+pause, +forget, +assign etc.) |
| `nomos-api/` | 679 | 14 | PARTIAL | Massiv erweitern (Auth, Proxy, Tasks, Approvals) |
| `nomos-console/` | ~500 | 1 E2E | REAL aber minimal | **ARCHIV → Neu bauen** |
| `nomos-plugin/` | 250 | 0 | REAL (Slash Commands) | **ARCHIV → Neu bauen** (Runtime Hooks) |

**Summe v1:** ~2.850 Zeilen Code, 92 Tests, 5 API Endpoints

---

## Phasen-Uebersicht

```
Phase 0: Repo-Reorganisation (1 Session)
  └── Archivieren, Struktur, CLAUDE.md aktualisieren

Phase 1: Foundation — PARALLEL (A + E)
  ├── A: NomOS Plugin Core (TypeScript, OpenClaw Hooks)
  └── E: Auth + Security (Python, JWT, 2FA, Recovery Key)

Phase 2: Core Logic — PARALLEL (B + C), abhaengig von A
  ├── B: Control Plane (Heartbeat, Tasks, Approvals, Budget)
  └── C: Compliance Runtime (PII Filter, Kill Switch, Art.50, Gate v2)

Phase 3: Integration — abhaengig von A + C
  └── D: Honcho Integration (Memory, Firmenwissen, Retention, DSGVO Forget)

Phase 4: API — abhaengig von A + B + C + D + E
  └── F: API v2 (Fleet, Tasks, Approvals, Audit, Kosten, Proxy, Admin)

Phase 5: User Facing — PARALLEL (G + H), abhaengig von F
  ├── G: CLI v2 (hire/kill/pause/retire/forget/assign/deploy/patch)
  └── H: Console Command Center (Stitch-Design, WCAG, alle Panels)

Phase 6: Ship — abhaengig von ALLEM
  └── I: CI/CD + Customer Delivery (Pipeline, E2E, Deploy, Patch, Rollback)
```

### Abhaengigkeits-Graph

```
        Phase 0
           |
     +-----+-----+
     |           |
    [A]         [E]        ← Phase 1 (parallel)
     |           |
  +--+--+       |
  |     |       |
 [B]   [C]      |         ← Phase 2 (B+C parallel, beide brauchen A)
  |     |       |
  |   +-+-+     |
  |   |   |     |
  |  [D]  |     |         ← Phase 3 (D braucht A+C)
  |   |   |     |
  +---+---+-----+
        |
       [F]                 ← Phase 4 (braucht A+B+C+D+E)
        |
     +--+--+
     |     |
    [G]   [H]              ← Phase 5 (parallel)
     |     |
     +--+--+
        |
       [I]                 ← Phase 6
```

---

## Phase 0: Repo-Reorganisation

**Ziel:** Saubere Basis schaffen. Altes archivieren, neue Struktur aufsetzen.
**Plan-Dokument:** Kein eigener Plan — wird inline in diesem Dokument definiert.
**Dauer:** 1 Session

### 0.1 Archivieren

```
Verschieben nach _archive/:
  nomos-console/     → _archive/console-v1/    (wird komplett neu gebaut in Phase 5)
  nomos-plugin/      → _archive/plugin-v1/     (wird komplett neu gebaut in Phase 1)
  schemas/           → _archive/schemas-v1/    (Schema ist in manifest.py)
  docs/plans/        → _archive/plans-v1/      (alte Plaene, ersetzt durch diesen)

BEHALTEN (unveraendert):
  nomos-cli/         → Kern-Library, wird erweitert
  nomos-api/         → API, wird massiv erweitert
  templates/         → Agent-Templates, wird erweitert
  docker-compose.yml → wird erweitert
  docs/ (ausser plans/) → Doku bleibt
```

### 0.2 Neue Verzeichnisstruktur

```
nomos/
├── _archive/                    # Archivierte v1-Komponenten
│   ├── console-v1/
│   ├── plugin-v1/
│   ├── schemas-v1/
│   └── plans-v1/
│
├── nomos-cli/                   # Python Core Library (BEHALTEN + ERWEITERN)
│   ├── nomos/core/              # Manifest, Gate, HashChain, Forge, Events, Compliance
│   │   ├── manifest.py          # +Budget, +Approval, +Memory Config
│   │   ├── gate.py              # +9 neue Dokumente (5→14)
│   │   ├── hash_chain.py        # Unveraendert
│   │   ├── forge.py             # +Budget, +Approval, +Memory Setup
│   │   ├── compliance_engine.py # Unveraendert
│   │   ├── manifest_validator.py# Unveraendert
│   │   ├── events.py            # +10 neue Event Types
│   │   ├── pii_filter.py        # NEU — PII Runtime Engine (Phase C)
│   │   ├── budget.py            # NEU — Budget Tracking (Phase B)
│   │   └── retention.py         # NEU — Data Retention Engine (Phase D)
│   ├── nomos/cli.py             # +pause, +forget, +assign, +deploy, +patch
│   └── tests/                   # Erweitert pro Phase
│
├── nomos-api/                   # FastAPI Control Plane (BEHALTEN + MASSIV ERWEITERN)
│   ├── nomos_api/
│   │   ├── main.py              # +Auth Middleware, +Audit Middleware
│   │   ├── config.py            # +Redis, +Honcho Config
│   │   ├── database.py          # Unveraendert
│   │   ├── auth/                # NEU — JWT, 2FA, Recovery Key (Phase E)
│   │   │   ├── jwt.py
│   │   │   ├── totp.py
│   │   │   ├── recovery.py
│   │   │   └── middleware.py
│   │   ├── models/              # NEU — Erweiterte DB Models
│   │   │   ├── agent.py         # +Budget, +Status, +Heartbeat
│   │   │   ├── audit.py         # Erweitert
│   │   │   ├── user.py          # NEU (Phase E)
│   │   │   ├── task.py          # NEU (Phase B)
│   │   │   └── approval.py      # NEU (Phase B)
│   │   ├── services/            # NEU — Business Logic
│   │   │   ├── agent_service.py # Erweitert
│   │   │   ├── fleet_service.py # Erweitert
│   │   │   ├── heartbeat.py     # NEU (Phase B)
│   │   │   ├── task_dispatch.py # NEU (Phase B)
│   │   │   ├── approval.py      # NEU (Phase B)
│   │   │   ├── budget.py        # NEU (Phase B)
│   │   │   ├── honcho.py        # NEU (Phase D)
│   │   │   ├── pii.py           # NEU (Phase C)
│   │   │   └── incident.py      # NEU (Phase C)
│   │   ├── routers/             # NEU — Erweiterte API Routes
│   │   │   ├── agents.py        # Erweitert
│   │   │   ├── audit.py         # Erweitert
│   │   │   ├── compliance.py    # Erweitert
│   │   │   ├── fleet.py         # Erweitert
│   │   │   ├── health.py        # Unveraendert
│   │   │   ├── auth.py          # NEU (Phase E)
│   │   │   ├── tasks.py         # NEU (Phase B)
│   │   │   ├── approvals.py     # NEU (Phase B)
│   │   │   ├── costs.py         # NEU (Phase B)
│   │   │   ├── users.py         # NEU (Phase E)
│   │   │   ├── settings.py      # NEU (Phase F)
│   │   │   └── proxy.py         # NEU (Phase F)
│   │   └── schemas/             # Pydantic Request/Response Schemas
│   └── tests/                   # Erweitert pro Phase
│
├── nomos-plugin/                # NEU — TypeScript OpenClaw Plugin (Phase A)
│   ├── src/
│   │   ├── index.ts             # Plugin Entry, Gateway Registration
│   │   ├── hooks/               # 11 Runtime Hooks
│   │   │   ├── gateway-start.ts
│   │   │   ├── before-agent-start.ts
│   │   │   ├── before-tool-call.ts
│   │   │   ├── after-tool-call.ts
│   │   │   ├── tool-result-persist.ts
│   │   │   ├── message-received.ts
│   │   │   ├── message-sending.ts
│   │   │   ├── session-start.ts
│   │   │   ├── session-end.ts
│   │   │   ├── agent-end.ts
│   │   │   └── on-error.ts
│   │   ├── compliance/          # Compliance Gate Client
│   │   │   └── gate.ts
│   │   ├── audit/               # Audit Trail Client
│   │   │   └── chain.ts
│   │   ├── pii/                 # PII Filter Client
│   │   │   └── filter.ts
│   │   ├── budget/              # Budget Check Client
│   │   │   └── check.ts
│   │   ├── types.ts             # TypeScript Interfaces
│   │   └── config.ts            # Plugin Config
│   ├── tests/                   # vitest Tests
│   ├── tsconfig.json
│   └── package.json
│
├── nomos-console/               # NEU — Next.js 15 Command Center (Phase H)
│   ├── src/
│   │   ├── app/                 # App Router
│   │   │   ├── login/           # Auth Pages
│   │   │   ├── admin/           # Admin Panels (13 Routes)
│   │   │   ├── app/             # User Panels (4 Routes)
│   │   │   └── compliance/      # Officer Panels (1 Route)
│   │   ├── components/          # UI Components
│   │   │   ├── ui/              # Design System (Buttons, Cards, Tables, etc.)
│   │   │   ├── fleet/           # Agent Cards, Status Badges
│   │   │   ├── hire/            # Hire Wizard (4 Steps)
│   │   │   ├── chat/            # Embedded Chat (via Proxy)
│   │   │   ├── compliance/      # Compliance Matrix, Doc Viewer
│   │   │   ├── audit/           # Hash Chain Viewer, Export
│   │   │   ├── tasks/           # Task Board
│   │   │   ├── approvals/       # Approval Queue
│   │   │   └── shared/          # Header, Sidebar, Help System
│   │   ├── lib/                 # Utilities
│   │   │   ├── api.ts           # API Client
│   │   │   ├── auth.ts          # Auth Context
│   │   │   ├── speech/          # TTS/STT Integration
│   │   │   │   ├── tts.ts       # 3-Schichten TTS (Browser → Piper → Cloud)
│   │   │   │   └── stt.ts       # 3-Schichten STT (Browser → Whisper → Cloud)
│   │   │   └── i18n/            # DE + EN Translations
│   │   └── styles/              # Design System (Light + Dark)
│   ├── e2e/                     # Playwright E2E Tests
│   ├── next.config.ts
│   └── package.json
│
├── templates/                   # Agent Templates (erweitern)
│   ├── external-secretary/      # Mani Template (existiert)
│   └── compliance-red-teamer/   # Rico Template (NEU)
│       ├── manifest.yaml
│       ├── soul.md
│       └── test-suite.yaml
│
├── docker-compose.yml           # Erweitert (+Valkey, +Honcho, +Piper, +Whisper)
├── docker-compose.dev.yml       # NEU — Dev Stack
├── .env.example                 # Erweitert
│
├── docs/
│   ├── superpowers/
│   │   ├── specs/               # Design Spec v3
│   │   └── plans/               # Implementation Plans
│   │       ├── 2026-03-24-nomos-v2-master-plan.md    # DIESES DOKUMENT
│   │       ├── 2026-03-24-phase-0-repo-reorg.md      # Detailplan Phase 0
│   │       ├── 2026-03-2X-sub-A-plugin-core.md       # Detailplan Sub-Projekt A
│   │       ├── 2026-03-2X-sub-B-control-plane.md     # Detailplan Sub-Projekt B
│   │       ├── 2026-03-2X-sub-C-compliance-rt.md     # Detailplan Sub-Projekt C
│   │       ├── 2026-03-2X-sub-D-honcho.md            # Detailplan Sub-Projekt D
│   │       ├── 2026-03-2X-sub-E-auth.md              # Detailplan Sub-Projekt E
│   │       ├── 2026-03-2X-sub-F-api-v2.md            # Detailplan Sub-Projekt F
│   │       ├── 2026-03-2X-sub-G-cli-v2.md            # Detailplan Sub-Projekt G
│   │       ├── 2026-03-2X-sub-H-console.md           # Detailplan Sub-Projekt H
│   │       └── 2026-03-2X-sub-I-cicd.md              # Detailplan Sub-Projekt I
│   ├── de/                      # Deutsche Doku (erweitern)
│   └── *.md                     # Bestehende Doku (behalten)
│
├── .claude/
│   ├── CLAUDE.md                # Aktualisiert (neue Struktur, neue Regeln)
│   └── agents/                  # Agent-Definitionen pro Sub-Projekt
│
├── scripts/
│   └── e2e-test.sh              # Erweitert
│
└── README.md                    # Aktualisiert
```

### 0.3 CLAUDE.md aktualisieren

Die `.claude/CLAUDE.md` wird aktualisiert mit:
- Neue Repo-Struktur (oben)
- Verweis auf diesen Master-Plan
- Aktuelle Bestandsaufnahme

### 0.4 Rico Template anlegen

```
templates/compliance-red-teamer/
  ├── manifest.yaml    # Aus Feedback-Dokument
  ├── soul.md          # Aus Feedback-Dokument
  └── test-suite.yaml  # 80+ Tests, 17 Sektionen
```

### 0.5 Entscheidungen (ALLE GETROFFEN — 25.03.2026)

```
1. LLM-Anbieter: KUNDENENTSCHEIDUNG — NomOS ist provider-agnostic
   → Manifest speichert llm_provider + llm_location
   → Compliance-Docs passen sich automatisch an (TIA bei US-Cloud)

2. Honcho Deriver LLM: KUNDENENTSCHEIDUNG — wie #1

3. Fair Source: FCL (Fair Core License) — 3 Agents gratis
   → Voller Funktionsumfang (Reports, Audit, Compliance)
   → Ab Agent 4 → kommerzielle Lizenz
   → Fleet API enforced count
   → Hire-Wizard: "3/3 Mitarbeiter — [Lizenz-Link]"
   → Change License: Apache 2.0 nach 2 Jahren

4. TTS/STT: 3-SCHICHTEN Accessibility
   → Schicht 1: Browser-native (Web Speech API) — Standard, null Setup
   → Schicht 2: Piper TTS (MIT) + Whisper.cpp (MIT) — lokal Docker
   → Schicht 3: Cloud API (optional, Kundenentscheidung)
   → UI: 🎤 Mikrofon + 🔊 Vorlese-Button in JEDEM Panel
   → Leitsatz: "Jeder entwickelt fuer sich, wir fuer alle."

5. Mobile: JA — responsive (kein Mobile-First)

6. Redis → VALKEY (BSD-3 statt AGPL-3.0, Drop-in Replacement)
```

### 0.6 Feedback archivieren

```
docs/reviews/2026-03-24-external-feedback-nomos-v2.md
  ← Kopie von "feedback nomos.txt" (Original auf Desktop)
```

---

## Sub-Projekt A: NomOS Plugin Core

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-A-plugin-core.md`
**Abhaengigkeit:** Phase 0 abgeschlossen
**Parallelisierbar mit:** E (Auth)

### Scope

Das OpenClaw Plugin das sich beim Gateway-Start registriert und 11 Runtime Hooks ausfuehrt. Jeder Hook ruft die NomOS API auf. Das Plugin ist die BRUECKE zwischen OpenClaw Gateway und NomOS Control Plane.

### User Stories

```
Als KMU-Chef will ich dass JEDE Agent-Nachricht automatisch auf PII gefiltert wird
  → Hook: message_received, tool_result_persist

Als KMU-Chef will ich dass JEDE Agent-Antwort als "KI-generiert" markiert wird
  → Hook: message_sending (Art. 50)

Als KMU-Chef will ich dass kein Agent ohne vollstaendige Compliance-Docs startet
  → Hook: before_agent_start (Compliance Gate)

Als KMU-Chef will ich dass destruktive Tool-Calls genehmigt werden muessen
  → Hook: before_tool_call (Approval Gate + Budget Check)

Als KMU-Chef will ich dass jeder Tool-Call im Audit-Trail landet
  → Hook: after_tool_call (Hash Chain Entry)

Als KMU-Chef will ich dass bei Fehlern der Agent automatisch pausiert
  → Hook: on_error (Auto-Pause + Incident Detection)
```

### Dateien

```
NEU erstellen:
  nomos-plugin/src/index.ts                    # Plugin Entry, Hook Registration
  nomos-plugin/src/hooks/gateway-start.ts      # Fleet Sync, Health Check
  nomos-plugin/src/hooks/before-agent-start.ts # Compliance Gate Call
  nomos-plugin/src/hooks/before-tool-call.ts   # Safety + Budget + Approval
  nomos-plugin/src/hooks/after-tool-call.ts    # Audit Logger (Hash Chain)
  nomos-plugin/src/hooks/tool-result-persist.ts# PII Filter Call
  nomos-plugin/src/hooks/message-received.ts   # Session Tracking, Kosten-Start
  nomos-plugin/src/hooks/message-sending.ts    # Art. 50 Label, Disclosure
  nomos-plugin/src/hooks/session-start.ts      # Honcho Session Create/Resume
  nomos-plugin/src/hooks/session-end.ts        # Kosten, Summary, Dreamer
  nomos-plugin/src/hooks/agent-end.ts          # Final Audit, Compliance Close
  nomos-plugin/src/hooks/on-error.ts           # Auto-Pause, Incident
  nomos-plugin/src/api-client.ts               # HTTP Client fuer NomOS API
  nomos-plugin/src/types.ts                    # TypeScript Interfaces
  nomos-plugin/src/config.ts                   # Plugin Config (API URL, Auth)
  nomos-plugin/tests/*.test.ts                 # vitest Tests pro Hook
  nomos-plugin/package.json
  nomos-plugin/tsconfig.json
  nomos-plugin/vitest.config.ts

BENOETIGT (von NomOS API — volle Endpoints kommen in Phase B-F):
  POST /api/compliance/gate       → Compliance Check
  POST /api/audit/entry           → Hash Chain Entry
  POST /api/pii/filter            → PII Maskierung
  POST /api/budget/check          → Budget Pruefung
  POST /api/approvals/request     → Approval Queue
  POST /api/agents/{id}/heartbeat → Heartbeat

  HINWEIS: Phase A Tests nutzen einen Mock API Server (vitest mock),
  NICHT Skeleton-Endpoints. Keine Platzhalter-Endpoints (S9/R10).
  Die echten Endpoints werden in den jeweiligen Phasen implementiert.
```

### Interfaces (TypeScript)

```typescript
// Jeder Hook bekommt ein Event-Objekt und gibt eine Action zurueck
interface HookEvent {
  type: string;
  agent_id: string;
  session_id?: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

interface HookResult {
  action: 'allow' | 'block' | 'modify';
  reason?: string;
  modified_payload?: Record<string, unknown>;
}

// API Client Interface
interface NomOSApiClient {
  checkCompliance(agentId: string): Promise<{ passed: boolean; missing: string[] }>;
  addAuditEntry(entry: AuditEntry): Promise<{ hash: string }>;
  filterPII(text: string): Promise<{ filtered: string; found: PIIMatch[] }>;
  checkBudget(agentId: string, estimatedCost: number): Promise<{ allowed: boolean; remaining: number }>;
  requestApproval(request: ApprovalRequest): Promise<{ queued: boolean; id: string }>;
}
```

### Test-Strategie

```
Unit Tests (vitest):
  - Jeder Hook: korrektes Event-Handling, korrekte API-Calls
  - API Client: Request/Response Mapping, Error Handling
  - Config: Laden, Validierung, Defaults

Integration Tests:
  - Plugin → Mock API Server → Hook-Kette verifizieren
  - Gateway Start → Fleet Sync Ablauf
  - Message Flow: received → sending → persist

Compliance Tests:
  - Agent ohne Docs → before_agent_start → BLOCKED
  - Destruktiver Tool-Call → before_tool_call → APPROVAL_REQUIRED
  - Budget ueberschritten → before_tool_call → BLOCKED
  - PII in Message → tool_result_persist → MASKED
  - Error → on_error → AUTO_PAUSE
```

### Erfolgs-Kriterien

- [ ] 11 Hooks registriert und ausfuehrbar
- [ ] Jeder Hook hat mindestens 3 Tests
- [ ] Plugin laesst sich in OpenClaw Gateway laden
- [ ] Compliance Gate blockt Agent ohne Docs
- [ ] Art. 50 Label wird in jede Antwort eingefuegt
- [ ] PII wird vor Persistierung maskiert
- [ ] Alle Tests gruen

---

## Sub-Projekt B: Control Plane

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-B-control-plane.md`
**Abhaengigkeit:** A abgeschlossen
**Parallelisierbar mit:** C (Compliance Runtime)

### Scope

Heartbeat-System, Task Dispatch, Approval Gates, Budget Enforcement. Die Steuerungsschicht die aus NomOS mehr als ein UI macht — eine echte Control Plane.

### User Stories

```
Als KMU-Chef will ich sehen ob meine Agents online sind
  → Heartbeat System (30s Intervall, STALE/OFFLINE Detection)

Als KMU-Chef will ich meinen Agents Aufgaben zuweisen koennen
  → Task Dispatch (queued → assigned → running → review → done)

Als KMU-Chef will ich dass kritische Aktionen genehmigt werden muessen
  → Approval Gates (externe API, Loeschung, Export, Budget-Ueberschreitung)

Als KMU-Chef will ich dass Kosten automatisch kontrolliert werden
  → Budget Enforcement (80% Warnung, 100% Auto-Pause)

Als KMU-Chef will ich jede Config-Aenderung zuruecksetzen koennen
  → Config Revisioning (Versionshistorie + Rollback)

Als KMU-Chef will ich bis zu 3 Mitarbeiter kostenlos einsetzen koennen
  → FCL Enforcement: Fleet API count, Hire blockiert ab 4, voller Funktionsumfang
```

### Dateien

```
NEU erstellen (Python — nomos-api):
  nomos-api/nomos_api/services/heartbeat.py     # Heartbeat-Empfaenger + STALE/OFFLINE
  nomos-api/nomos_api/services/task_dispatch.py  # Task CRUD + Lifecycle + Timeout
  nomos-api/nomos_api/services/approval.py       # Approval Queue + Delegation
  nomos-api/nomos_api/services/budget.py         # Budget Tracking + Enforcement
  nomos-api/nomos_api/services/config_revision.py# Config Versioning + Rollback
  nomos-api/nomos_api/models/task.py             # SQLAlchemy: Task Model
  nomos-api/nomos_api/models/approval.py         # SQLAlchemy: Approval Model
  nomos-api/nomos_api/models/config_revision.py  # SQLAlchemy: Config Revision Model
  nomos-api/nomos_api/routers/tasks.py           # REST: /api/tasks/*
  nomos-api/nomos_api/routers/approvals.py       # REST: /api/approvals/*
  nomos-api/nomos_api/routers/costs.py           # REST: /api/costs/*

ERWEITERN:
  nomos-api/nomos_api/models/agent.py            # +budget, +heartbeat_at, +status
  nomos-api/nomos_api/routers/agents.py          # +PATCH (pause/resume/kill) + config rollback
  nomos-cli/nomos/core/manifest.py               # +BudgetConfig, +ApprovalConfig
  nomos-cli/nomos/core/events.py                 # +task.*, +approval.*, +budget.*, +config.*

TESTS:
  nomos-api/tests/test_heartbeat.py
  nomos-api/tests/test_tasks.py
  nomos-api/tests/test_approvals.py
  nomos-api/tests/test_budget.py
  nomos-api/tests/test_config_revision.py        # Config Versioning + Rollback
  nomos-cli/tests/test_manifest_v2.py            # Budget + Approval Fields
```

### Erfolgs-Kriterien

- [ ] Heartbeat empfangen, STALE nach 5min, OFFLINE nach 10min
- [ ] Task Lifecycle vollstaendig (queued → done)
- [ ] Approval Queue mit Timeout + Delegation
- [ ] Budget 80% Warnung, 100% Auto-Pause
- [ ] Config Revisioning mit Rollback
- [ ] Alle Aktionen erzeugen Audit Entries

---

## Sub-Projekt C: Compliance Runtime

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-C-compliance-rt.md`
**Abhaengigkeit:** A abgeschlossen
**Parallelisierbar mit:** B (Control Plane)

### Scope

PII Filter Runtime Engine, Kill Switch Enforcement, Art. 50 Labeling, Compliance Gate v2 (5→14 Dokumente), Incident Detection + Response (Art. 33/34 DSGVO).

### User Stories

```
Als KMU-Chef will ich dass PII automatisch maskiert wird bevor sie gespeichert wird
  → PII Filter: Regex + Pattern + NER (konfigurierbar pro Agent)

Als KMU-Chef will ich dass ich jeden Agent SOFORT stoppen kann
  → Kill Switch: Admin + User (Art. 14), <5s Reaktionszeit

Als KMU-Chef will ich dass jede Agent-Antwort als KI-generiert markiert ist
  → Art. 50 Label: "KI-generiert" + ai_disclosure aus Manifest

Als KMU-Chef will ich dass bei einer Datenpanne automatisch gewarnt wird
  → Incident Detection: PII in Logs, unbekannte Endpoints, Hash-Tamper
  → 72h Timer + Checkliste + Meldungsvorlage

Als KMU-Chef will ich 14 Compliance-Dokumente automatisch generiert
  → Gate v2: 5 existierend + 9 neue (AVV, Risk Mgmt, TIA, etc.)
```

### Dateien

```
NEU erstellen (Python — nomos-cli):
  nomos-cli/nomos/core/pii_filter.py            # PII Runtime: Regex + Pattern + NER
  nomos-cli/nomos/core/incident.py               # Incident Detection + 72h Timer

ERWEITERN:
  nomos-cli/nomos/core/gate.py                   # +9 Dokumente (6-14)
  nomos-cli/nomos/core/events.py                 # +incident.*, +pii.*, +kill_switch.*

NEU erstellen (Python — nomos-api):
  nomos-api/nomos_api/services/pii.py            # PII Service (API Layer)
  nomos-api/nomos_api/services/incident.py       # Incident Service
  nomos-api/nomos_api/routers/incidents.py       # REST: /api/incidents/*

TESTS:
  nomos-cli/tests/test_pii_filter.py             # PII Erkennung + Maskierung
  nomos-cli/tests/test_gate_v2.py                # 14 Dokumente
  nomos-cli/tests/test_incident.py               # Incident Detection
  nomos-api/tests/test_pii_api.py
  nomos-api/tests/test_incidents.py
```

### PII Filter Architektur

```
Eingabe: Rohtext (User-Nachricht, Tool-Result, Agent-Antwort)

Pipeline (sequenziell):
  1. Regex-Erkennung:
     - Email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/
     - Telefon: /(\+?\d{1,4}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{1,9}/
     - IBAN: /[A-Z]{2}\d{2}[A-Z0-9]{4,}/
     - Steuernummer: /\d{2,3}\/?\d{3,4}\/?\d{4,5}/

  2. Pattern Matching (konfigurierbar):
     - Adressen (Strasse + Hausnummer + PLZ + Ort)
     - Namen (Vor- + Nachname, konfigurierbare Wortliste)

  3. NER (Named Entity Recognition):
     - Default bei high-risk Agents (Pflicht)
     - Optional bei limited/minimal
     - Modell: spaCy de_core_news_sm + en_core_web_sm
     - Entitaeten: PERSON, ORG, LOC, GPE

Ausgabe:
  {
    "filtered_text": "Bitte kontaktieren Sie [EMAIL_REDACTED] unter [PHONE_REDACTED]",
    "found": [
      {"type": "email", "original": "max@example.com", "position": [25, 40]},
      {"type": "phone", "original": "+43 1 234 5678", "position": [47, 62]}
    ],
    "pii_count": 2
  }
```

### Erfolgs-Kriterien

- [ ] PII Filter erkennt Email, Telefon, IBAN, Steuernummer, Adressen, Namen
- [ ] Maskierung BEVOR Daten in Honcho/DB landen
- [ ] Kill Switch stoppt Agent in <5 Sekunden
- [ ] Art. 50 Label in jeder Agent-Antwort
- [ ] 14 Compliance-Dokumente generiert + signiert
- [ ] Incident Detection bei PII in Logs, Hash-Tamper
- [ ] 72h Timer + Checkliste
- [ ] NER optional zuschaltbar (Default bei high-risk)

---

## Sub-Projekt D: Honcho Integration

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-D-honcho.md`
**Abhaengigkeit:** A + C abgeschlossen
**Nicht parallelisierbar** (braucht PII Filter aus C)

### Scope

Memory Management via Honcho API, Firmenwissen (Company Workspace), Agent-Isolation, Retention Engine, DSGVO Art. 17 (Forget), Deriver-Kontrolle.

### User Stories

```
Als KMU-Chef will ich dass meine Agents Firmenwissen lesen koennen
  → Company Workspace (read-only Collections)

Als KMU-Chef will ich dass Agents NUR ihren eigenen Bereich beschreiben
  → Agent Workspace Isolation (Scoped Tokens)

Als KMU-Chef will ich dass alte Daten automatisch geloescht werden
  → Retention Engine (90 Tage Default, konfigurierbar)

Als KMU-Chef will ich dass ich Kundendaten auf Anfrage loeschen kann
  → nomos forget (DSGVO Art. 17)

Als KMU-Chef will ich dass der Agent aus Gespraechen lernt (mit Einwilligung)
  → Deriver-Kontrolle (observe_me Flag)
```

### Dateien

```
NEU erstellen (Python):
  nomos-cli/nomos/core/retention.py              # Retention Engine (Cron)
  nomos-api/nomos_api/services/honcho.py         # Honcho API Client
  nomos-api/nomos_api/services/workspace.py      # Workspace Mount/Unmount
  nomos-api/nomos_api/routers/workspace.py       # REST: /api/workspace/*
  nomos-api/nomos_api/routers/memory.py          # REST: /api/memory/*

ERWEITERN:
  nomos-cli/nomos/core/manifest.py               # +MemoryConfig (namespace, isolation, retention)
  nomos-cli/nomos/cli.py                         # +forget, +workspace mount/unmount

TESTS:
  nomos-cli/tests/test_retention.py
  nomos-api/tests/test_honcho.py
  nomos-api/tests/test_workspace.py
```

### Workspace Isolation (aus Spec v3)

```
Technische Enforcement:
  1. Honcho API Scoping:
     Agent "mani": scope = workspace:mani:read,write + workspace:company:read
     Agent "lisa": scope = workspace:lisa:read,write + workspace:company:read

  2. NomOS API Proxy Validierung:
     JWT agent_id == Workspace im Request
     Mismatch → 403 "workspace_access_denied" + Audit Entry

  3. Sub-Agent Vererbung:
     Sub-Agents erben Parent-Scope, eigene Session-IDs
     Budget gegen Parent-Agent gerechnet

  4. Mount/Unmount Lifecycle:
     nomos workspace mount --agent "mani" --collection "brand-guidelines"
     nomos workspace unmount --agent "mani" --collection "brand-guidelines"
     Bei Retire: automatisches Unmount + Scope-Revocation
```

### Erfolgs-Kriterien

- [ ] Honcho API Client funktioniert (Sessions, Messages, Collections)
- [ ] Company Workspace read-only fuer alle Agents
- [ ] Agent kann NUR eigenen Workspace beschreiben
- [ ] Cross-Agent Zugriff → 403 + Audit Entry
- [ ] Retention Engine loescht nach Ablauf + Audit Entry
- [ ] nomos forget loescht PII, laesst pseudonymisierten Audit
- [ ] Deriver-Kontrolle (observe_me nur mit Einwilligung)

---

## Sub-Projekt E: Auth + Security

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-E-auth.md`
**Abhaengigkeit:** Phase 0 abgeschlossen
**Parallelisierbar mit:** A (Plugin Core)

### Scope

JWT-basierte Authentifizierung, optionale 2FA (TOTP), Recovery Key (BIP-39), Rollen (Admin/User/Compliance Officer), Rate Limiting, Transport Security.

### User Stories

```
Als KMU-Chef will ich mich sicher einloggen koennen
  → JWT + HttpOnly Cookie + optional 2FA

Als KMU-Chef will ich mein Konto wiederherstellen wenn ich Passwort + 2FA verliere
  → Recovery Key (12 BIP-39 Woerter)

Als KMU-Chef will ich dass meine Mitarbeiter nur sehen was sie duerfen
  → Rollen: Admin (alles), User (eigene Agents), Officer (Compliance read-only)

Als KMU-Chef will ich dass die API gegen Brute-Force geschuetzt ist
  → Rate Limiting + Lockout nach 5 Fehlversuchen
```

### Dateien

```
NEU erstellen (Python — nomos-api):
  nomos-api/nomos_api/auth/jwt.py                # JWT Token Generation + Validation
  nomos-api/nomos_api/auth/totp.py               # TOTP 2FA (pyotp)
  nomos-api/nomos_api/auth/recovery.py           # BIP-39 Recovery Key (mnemonic)
  nomos-api/nomos_api/auth/middleware.py          # Auth Middleware (Role Check)
  nomos-api/nomos_api/auth/rate_limiter.py        # Rate Limiting (Redis-backed)
  nomos-api/nomos_api/models/user.py              # SQLAlchemy: User Model
  nomos-api/nomos_api/routers/auth.py             # REST: /api/auth/*
  nomos-api/nomos_api/routers/users.py            # REST: /api/users/*

TESTS:
  nomos-api/tests/test_jwt.py
  nomos-api/tests/test_totp.py
  nomos-api/tests/test_recovery.py
  nomos-api/tests/test_auth_middleware.py
  nomos-api/tests/test_rate_limiter.py
  nomos-api/tests/test_users.py
```

### Rollen-Matrix

```
             | Admin | User | Officer |
-------------|-------|------|---------|
Fleet sehen  |  ✓    |  ✓*  |   ✗    |   * nur zugewiesene
Agent Config |  ✓    |  ✗   |   ✗    |
Kill/Pause   |  ✓/✓  |  ✗/✓ |   ✗/✗  |   User: NUR Pause (Art. 14)
Hire         |  ✓    |  ✗   |   ✗    |
Audit        |  ✓    |  ✗   |   ✓    |   Officer: read-only
Compliance   |  ✓    |  ✗   |   ✓    |   Officer: read-only
Budget/Kosten|  ✓    |  ✗*  |   ✗    |   * nur eigene Tasks
Approvals    |  ✓    |  ✓*  |   ✗    |   * nur delegierte
Settings     |  ✓    |  ✗   |   ✗    |
Users        |  ✓    |  ✗   |   ✗    |
Chat lesen   |  ✓    |  ✓*  |   ✗    |   * nur eigene
Export       |  ✓    |  ✗   |   ✓    |
```

### Erfolgs-Kriterien

- [ ] JWT Login (Email + Passwort) funktioniert
- [ ] 2FA (TOTP) optional aktivierbar
- [ ] Recovery Key generiert, bcrypt-gehashed, einmal angezeigt
- [ ] Recovery Flow: 12 Woerter → neues Passwort
- [ ] 3 Rollen mit korrekter Rechte-Separation
- [ ] Rate Limiting: 5 Fehlversuche → 15min Lockout
- [ ] Session Timeout: 8h (Admin), 24h (User)
- [ ] Jeder Auth-Event im Audit Trail

---

## Sub-Projekt F: API v2

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-F-api-v2.md`
**Abhaengigkeit:** A + B + C + D + E abgeschlossen
**Nicht parallelisierbar** (integriert alles)

### Scope

Alle Services zu einer kohaerenten REST API zusammenfuehren. API Proxy fuer OpenClaw Gateway. Admin-Endpoints. Audit Middleware (jeder Call wird geloggt).

### Endpoints (Uebersicht)

```
Auth:
  POST   /api/auth/login           → JWT Token
  POST   /api/auth/logout          → Session invalidieren
  POST   /api/auth/2fa/setup       → TOTP QR Code
  POST   /api/auth/2fa/verify      → TOTP verifizieren
  POST   /api/auth/recovery        → Recovery Key Flow

Fleet:
  GET    /api/fleet                 → Alle Agents (gefiltert nach Rolle)
  GET    /api/agents/{id}           → Agent Detail
  POST   /api/agents                → Agent erstellen (Hire)
  PATCH  /api/agents/{id}           → Agent Config aendern
  POST   /api/agents/{id}/pause     → Pausieren (User + Admin)
  POST   /api/agents/{id}/resume    → Fortsetzen (Admin, oder User wenn erlaubt)
  POST   /api/agents/{id}/kill      → Permanent stoppen (Admin only)
  POST   /api/agents/{id}/retire    → Graceful Kill + Archiv
  POST   /api/agents/{id}/heartbeat → Heartbeat empfangen

Tasks:
  GET    /api/tasks                 → Task-Liste (gefiltert)
  POST   /api/tasks                 → Task erstellen
  PATCH  /api/tasks/{id}            → Status aendern
  GET    /api/tasks/{id}            → Task Detail

Approvals:
  GET    /api/approvals             → Offene Freigaben
  POST   /api/approvals/{id}/approve → Genehmigen
  POST   /api/approvals/{id}/reject  → Ablehnen

Compliance:
  GET    /api/agents/{id}/compliance → Compliance Status
  POST   /api/compliance/gate        → Compliance Gate Check
  GET    /api/compliance/matrix      → Alle Agents x alle Gesetze

Audit:
  GET    /api/audit                  → Audit Trail (gefiltert, paginiert)
  GET    /api/audit/export           → JSONL / PDF Export
  POST   /api/audit/entry            → Neuen Eintrag hinzufuegen
  GET    /api/audit/verify/{id}      → Hash Chain verifizieren

Costs:
  GET    /api/costs                  → Kosten-Uebersicht (alle Agents)
  GET    /api/costs/{agent_id}       → Kosten pro Agent

Memory:
  GET    /api/workspace/{agent_id}   → Agent Workspace Info
  POST   /api/workspace/mount        → Collection mounten
  POST   /api/workspace/unmount      → Collection unmounten
  POST   /api/pii/filter             → PII maskieren

Users:
  GET    /api/users                  → User-Liste (Admin)
  POST   /api/users                  → User erstellen
  PATCH  /api/users/{id}             → User Limits aendern
  DELETE /api/users/{id}             → User loeschen

Settings:
  GET    /api/settings               → System Settings
  PATCH  /api/settings               → Settings aendern

Proxy:
  POST   /api/proxy/chat             → OpenClaw Gateway Proxy
  GET    /api/proxy/status           → Gateway Status

Incidents:
  GET    /api/incidents              → Incident-Liste
  PATCH  /api/incidents/{id}         → Status aendern (gemeldet, geschlossen)

DSGVO:
  POST   /api/dsgvo/forget           → Art. 17 Loeschung
  POST   /api/dsgvo/export           → Art. 15 Auskunft

Health:
  GET    /health                     → System Health
```

### Erfolgs-Kriterien

- [ ] Alle Endpoints implementiert mit korrekter Auth + Role Check
- [ ] Audit Middleware loggt JEDEN API Call
- [ ] Proxy leitet korrekt an OpenClaw Gateway weiter
- [ ] Rate Limiting aktiv
- [ ] OpenAPI Spec generiert (Swagger UI)
- [ ] Alle Endpoints getestet (min. 2 Tests pro Endpoint)

---

## Sub-Projekt G: CLI v2

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-G-cli-v2.md`
**Abhaengigkeit:** F abgeschlossen
**Parallelisierbar mit:** H (Console)

### Scope

CLI erweitern um alle neuen Commands. CLI ruft NomOS API auf.

### Neue Commands

```
nomos pause <agent>                      # Temporaer pausieren
nomos resume <agent>                     # Wieder starten
nomos retire <agent>                     # Graceful Kill + Archiv
nomos forget <email>                     # DSGVO Art. 17
nomos assign <agent> --task "..."        # Task zuweisen
nomos deploy --target <server>           # Stack deployen
nomos patch --version <x.y.z>            # Update
nomos rollback                           # Letztes Patch rueckgaengig
nomos workspace mount --agent --collection
nomos workspace unmount --agent --collection
nomos incident list                      # Incidents anzeigen
nomos costs                              # Kosten-Uebersicht
nomos costs <agent>                      # Kosten pro Agent
```

### Erfolgs-Kriterien

- [ ] Alle Commands implementiert
- [ ] CLI ruft API auf (nicht direkt DB)
- [ ] Hilfe-Texte bilingual (DE + EN)
- [ ] Error Messages menschlich formuliert
- [ ] Jeder Command hat Tests

---

## Sub-Projekt H: Console (Command Center)

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-H-console.md`
**Abhaengigkeit:** F abgeschlossen
**Parallelisierbar mit:** G (CLI v2)

### Scope

Komplettes Next.js 15 Dashboard. Alle 13 Admin-Panels + 4 User-Panels + 1 Officer-Panel. Hire Wizard (4 Steps). Embedded Chat. WCAG 2.2 AA. TTS/STT (3-Schichten). Bilingual. Light + Dark Mode.

**Leitsatz:** *"Jeder entwickelt fuer sich, wir fuer alle."* — Accessibility ist Fundament, nicht Feature.

### Design-System (aus Spec)

```
Light Mode:
  Background: #FAFAFA | Cards: #FFFFFF | Primary: #4262FF | Text: #1A1A2E
  Headlines: Montserrat (bold) | Body: Geist Sans | Code: Geist Mono
  Border-Radius: 8px | Transitions: 150ms ease

Dark Mode:
  Background: #0a0a0a | Cards: #1a1919 | Text: #FFFFFF
  Gleiche Akzentfarben wie Light Mode

WCAG 2.2 AA:
  Kontrast min 4.5:1 | Focus 2px #4262FF | Zoom 200% | lang="de"
  axe-core: 0 critical + 0 serious | Keyboard Navigation
```

### Panels (18 total)

```
Admin (13):
  /admin/                    Dashboard (Team, Rechts-Status, Kosten, Gesundheit)
  /admin/team                Mein Team (Agent-Karten)
  /admin/team/{id}           Mitarbeiter-Profil
  /admin/compliance          Rechts-Check (Matrix)
  /admin/audit               Protokoll (Hash Chain Viewer)
  /admin/diagnostics         Gesundheitscheck
  /admin/hire                Neuen Mitarbeiter einstellen (4-Step Wizard)
  /admin/costs               Kosten
  /admin/approvals           Freigaben
  /admin/users               Nutzer
  /admin/settings            Einstellungen
  /admin/incidents           Vorfaelle
  /admin/tasks               Aufgaben (Admin-View)

User (4):
  /app/                      Meine Mitarbeiter
  /app/chat/{id}             Chat (Embedded via Proxy)
  /app/tasks                 Aufgaben
  /app/help                  Hilfe

Officer (1):
  /compliance/               Compliance Reports + Audit (read-only)
```

### Erfolgs-Kriterien

- [ ] Alle 18 Panels implementiert
- [ ] Hire Wizard funktioniert end-to-end
- [ ] Embedded Chat via Proxy
- [ ] WCAG 2.2 AA: axe-core 0 critical/serious
- [ ] Keyboard Navigation in allen Panels
- [ ] Bilingual DE + EN (Switch im Header)
- [ ] Light + Dark Mode
- [ ] Mitarbeiter-Metapher DURCHGEHEND (keine technischen Begriffe)
- [ ] Hilfe-System in jedem Panel ("?" Icon)
- [ ] Onboarding-Tour beim ersten Login
- [ ] TTS/STT Schicht 1 (Browser-native) in allen Panels
- [ ] TTS/STT Schicht 2 (Piper + Whisper) als optionaler Docker-Service
- [ ] Mikrofon-Button neben jedem Textfeld
- [ ] Vorlese-Button bei jedem Text-Block (Agent-Antworten, Reports, Fehler)
- [ ] Einstellungen → Barrierefreiheit (Quelle, Geschwindigkeit, Stimme)
- [ ] Playwright E2E Tests fuer alle kritischen Flows

---

## Sub-Projekt I: CI/CD + Customer Delivery

**Plan-Dokument:** `docs/superpowers/plans/2026-03-2X-sub-I-cicd.md`
**Abhaengigkeit:** ALLE vorherigen abgeschlossen
**Nicht parallelisierbar**

### Scope

GitHub Actions Pipeline, E2E Test Suite, Docker Image Build, Customer Deployment (nomos deploy), Patching (nomos patch), Rollback, Rico Red-Team Integration.

### Pipeline

```
Push/PR:
  → Lint (ruff + eslint + tsc --noEmit)
  → Unit Tests (pytest + vitest)
  → Docker Build (multi-stage)
  → Integration Tests (docker compose up, gegen echte Services)
  → E2E Tests (Playwright gegen laufenden Stack)
  → WCAG Scan (axe-core)
  → Security Scan (trivy, npm audit)
  → Compliance Tests (Agent ohne Docs → BLOCKED, PII → MASKED, etc.)
  → Build + Tag Artifacts

Release:
  → Semantic Version Tag
  → Docker Images → GHCR
  → Changelog
  → Release Notes
```

### Rico Integration

```
templates/compliance-red-teamer/
  ├── manifest.yaml       # Agent Manifest
  ├── soul.md             # SOUL.md (aus Feedback)
  └── test-suite.yaml     # 80+ Tests, 17 Sektionen

nomos hire "Rico" --role "Compliance Red Teamer" --risk high --budget 140 --test-mode
  → Automatischer woechentlicher Full-Scan
  → Auto-Pause bei kritischen Findings
```

### Erfolgs-Kriterien

- [ ] CI Pipeline: alle Checks gruen bei sauberem Code
- [ ] Docker Images bauen und starten
- [ ] nomos deploy auf frischer VM funktioniert
- [ ] nomos patch + rollback funktionieren
- [ ] Rico Template im Hire Wizard verfuegbar
- [ ] Rico Weekly Scan laeuft
- [ ] E2E: Hire → Chat → Audit → Kill (vollstaendiger Flow)

---

## Agent-Zuweisung (nach Phase 0)

| Sub-Projekt | Agent-Name | Worktree Branch | Model | Begruendung |
|-------------|-----------|-----------------|-------|-------------|
| A: Plugin Core | plugin-dev | `sub-a/plugin-core` | opus | Komplexe Hook-Architektur |
| B: Control Plane | control-dev | `sub-b/control-plane` | opus | Verteilte Systeme |
| C: Compliance RT | compliance-dev | `sub-c/compliance-rt` | opus | Legal + Security Logik |
| D: Honcho | memory-dev | `sub-d/honcho` | sonnet | API Integration |
| E: Auth | auth-dev | `sub-e/auth` | sonnet | Standard Auth Patterns |
| F: API v2 | api-dev | `sub-f/api-v2` | opus | Integriert alles |
| G: CLI v2 | cli-dev | `sub-g/cli-v2` | sonnet | CLI Erweiterung |
| H: Console | console-dev | `sub-h/console` | opus | Komplexes UI + A11y |
| I: CI/CD | devops-dev | `sub-i/cicd` | sonnet | Pipeline + Deploy |

**Jeder Agent bekommt:**
- Eigenen Worktree Branch (Isolation)
- Eigenen detaillierten TDD-Plan (Dokument in `docs/superpowers/plans/`)
- Scope-Beschraenkung auf sein Sub-Projekt
- Review-Checkpoint am Ende (code-reviewer Agent)

---

## Review-Checkpoints

| Nach Phase | Wer reviewed | Was wird geprueft |
|------------|-------------|-------------------|
| Phase 0 | Joe | Repo-Struktur, Archiv korrekt, CLAUDE.md aktuell |
| Phase 1 (A+E) | code-reviewer | Plugin Hooks registriert, Auth funktioniert |
| Phase 2 (B+C) | code-reviewer | Heartbeat, Budget, PII Filter, Kill Switch |
| Phase 3 (D) | code-reviewer | Honcho Integration, Workspace Isolation |
| Phase 4 (F) | code-reviewer + Joe | API Vollstaendigkeit, Proxy, OpenAPI Spec |
| Phase 5 (G+H) | code-reviewer + Joe | UI/UX, WCAG, Mitarbeiter-Metapher |
| Phase 6 (I) | Joe | E2E, Deploy auf Test-Server, Rico Red-Team |

**Zwischen den Phasen: KEIN Weiterarbeiten ohne Review-Freigabe.**

---

## Risiko-Mitigation

| Risiko | Mitigation |
|--------|-----------|
| OpenClaw Plugin SDK nicht dokumentiert | Phase A: SDK zuerst reverse-engineeren, Interfaces definieren |
| Honcho API nicht erreichbar | Phase D: Mock-Server fuer Tests, echte Integration spaeter |
| Console zu komplex (18 Panels) | Phase H: Panel-fuer-Panel, nicht alles auf einmal |
| Performance der 11 Hooks | Phase A: Async Calls, Redis Queue fuer non-blocking |
| 14 Doc Templates juristisch | VOR Release: Anwaltliche Pruefung (nicht Code-Scope) |
| WCAG 2.2 AA Compliance | Phase H: axe-core in CI, manuelle Pruefung am Ende |

---

## Geschaetzte Komplexitaet

| Phase | Sub-Projekt | Neue Dateien | Neue Tests | Aufwand (relativ) |
|-------|-------------|-------------|------------|-------------------|
| 0 | Repo-Reorg | 3-5 | 0 | Klein |
| 1 | A: Plugin | ~15 | ~30 | Gross |
| 1 | E: Auth | ~8 | ~20 | Mittel |
| 2 | B: Control | ~10 | ~20 | Mittel |
| 2 | C: Compliance | ~6 | ~15 | Mittel |
| 3 | D: Honcho | ~5 | ~10 | Mittel |
| 4 | F: API v2 | ~10 | ~30 | Gross |
| 5 | G: CLI v2 | ~3 | ~15 | Klein |
| 5 | H: Console | ~40 | ~25 | Sehr Gross |
| 6 | I: CI/CD | ~5 | ~10 | Mittel |
| **TOTAL** | | **~105** | **~175** | |

---

## Naechster Schritt

Phase 0 ausfuehren (Repo-Reorganisation), dann den detaillierten TDD-Plan fuer Sub-Projekt A (Plugin Core) schreiben.

---

---

## Anhang: Open-Source Lizenz-Audit

### Kern-Abhaengigkeiten

| Tool | Lizenz | Kommerziell frei? | Risiko |
|---|---|---|---|
| OpenClaw | MIT | Ja | Keins |
| NemoClaw | Apache 2.0 | Ja | Keins |
| Honcho | AGPL-3.0 | Ja (via API, kein Fork) | Gering — als Container, kein Code-Aenderung |
| PostgreSQL | PostgreSQL (BSD-artig) | Ja | Keins |
| Valkey | BSD-3 (Linux Foundation) | Ja | Keins |

### Python

| Tool | Lizenz | | Tool | Lizenz |
|---|---|---|---|---|
| FastAPI | MIT | | Pydantic | MIT |
| Click | BSD-3 | | pytest | MIT |
| ruff | MIT | | spaCy (NER) | MIT |
| pyotp (2FA) | MIT | | bcrypt | Apache 2.0 |
| PyJWT | MIT | | SQLAlchemy | MIT |
| psycopg | LGPL-3.0 | | | |

### TypeScript/Frontend

| Tool | Lizenz | | Tool | Lizenz |
|---|---|---|---|---|
| Next.js 15 | MIT | | React | MIT |
| Tailwind CSS | MIT | | Playwright | Apache 2.0 |
| vitest | MIT | | Zod | MIT |
| axe-core | MPL-2.0 | | | |

### TTS/STT

| Tool | Lizenz | Kommerziell frei? |
|---|---|---|
| Piper TTS | MIT (Core) | Ja |
| Whisper.cpp | MIT | Ja |
| Web Speech API | Browser-Feature | Ja |

### Infrastruktur

| Tool | Lizenz | Kommerziell frei? |
|---|---|---|
| Docker Engine | Apache 2.0 | Ja |
| Docker Compose | Apache 2.0 | Ja |
| GitHub Actions | Plattform | Ja (Free Tier) |

### NomOS selbst

| Aspekt | Entscheidung |
|---|---|
| Lizenz | FCL (Fair Core License) |
| Use Limitation | 3 Agents |
| Change License | Apache 2.0 |
| Change Date | 2 Jahre nach Release |

**Fazit:** Alle Abhaengigkeiten sind MIT, Apache 2.0, BSD oder gleichwertig. Einziges Copyleft ist Honcho (AGPL-3.0) — aber wir nutzen es als separaten Container via API, ohne den Code zu forken. Kein Lizenz-Risiko.

---

*Plan basiert auf: NomOS v2 Design Spec v4 (25.03.2026), Brand Bible V2, externes Feedback (8.7/10), Codebase-Analyse (92 Tests, 2.850 LOC v1), Lizenz-Audit (25.03.2026)*
