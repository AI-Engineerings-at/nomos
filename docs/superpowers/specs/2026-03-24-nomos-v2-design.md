# NomOS v2 — Design Specification

> **Status**: ENTWURF v3 — Nach 3-Rollen-Review + externem Feedback korrigiert
> **Datum**: 24.03.2026
> **Autor**: Claude (nach Joe-Korrekturen + Legal/Tech/UX Review)
> **Vorbilder**: Paperclip (Control Plane), Mission Control (Task Dispatch, 577 Tests), Stitch (Visual Inspiration)
> **Vorgaenger**: NomOS v1 (84 Tests Core Library, 1/10 Produkt — siehe GAP-Analyse)
> **Reviews**: Legal 6.1/10, Tech 6.4/10, UX 5.5/10 — Alle Luecken in v2 geschlossen
> **Externes Feedback**: 8.7/10 — 3 kritische Punkte in v3 eingearbeitet (Workspace-Isolation, Doc-Validierung, Rico Red-Team)

---

## 1. Was ist NomOS

NomOS (Nomos = Gesetz + OS) ist eine **Compliance Control Plane fuer OpenClaw/NemoClaw** die EU AI Act und DSGVO Konformitaet erzwingt. Kein eigenes Agent-Framework — eine Governance-Schicht die sich IN das bestehende Oekosystem einklinkt, alles ueberwacht, dokumentiert und bei Verstoessen blockiert.

**Fuer wen:** KMU-Geschaeftsfuehrer (1-50 MA) im DACH-Raum die AI-Agenten einsetzen und legal compliant sein muessen. EU AI Act Deadline: 02.08.2026.

**Lizenz:** Fair Source — 3 Agents kostenlos, ab 4 kommerziell.

**Deployment:** `docker compose up -d` auf dem Server des Kunden. Standalone. Keine Cloud-Abhaengigkeit.

**Company Soul:** Jedes Produkt = Enterprise Value. Nicht "hier ist eine Datei" sondern ein fertiges System das sofort funktioniert. 6 Pflicht-Mehrwerte (Enterprise-Architektur, Anleitung im Produkt, HW/Budget Empfehlungen, Top-5 Fehlerbehebung, Bilingual DE+EN, Sofort lauffaehig).

---

## 2. Kern-Entscheidung: NomOS ist der EINZIGE Zugang

**Problem:** OpenClaw hat ein eigenes Dashboard. NemoClaw hat einen Terminal-Wizard. Wenn der User an NomOS vorbei kann, koennen wir nichts garantieren — keine Compliance, kein Audit, keine Sicherheit.

**Entscheidung:** NomOS Console ERSETZT alle originalen UIs. OpenClaw, NemoClaw und Honcho laufen headless (nur API). Der Kunde oeffnet einen Browser, sieht NomOS, und sonst nichts.

```
WAS DER KUNDE SIEHT:
  Browser → NomOS Console (Port 3040)
  → Alles: Hire, Chat, Monitor, Kill, Compliance, Audit

WAS DER KUNDE NICHT SIEHT:
  OpenClaw Gateway (headless, kein eigenes UI)
  NemoClaw (headless, Container via API)
  Honcho (headless, Memory via API)
  PostgreSQL, Redis (Infrastruktur)
```

**Vom Original behalten (headless, unter der Haube):**

| Komponente | Was wir behalten | Warum |
|------------|-----------------|-------|
| OpenClaw Gateway Engine | Message Routing, LLM Calls, Tool Execution | Kern-Funktionalitaet |
| OpenClaw Plugin System | NomOS registriert sich als Plugin | Integrationspunkt |
| OpenClaw Session Management | Sessions, Messages, History | Funktioniert |
| OpenClaw Workspace/Bootstrap | AGENTS.md, SOUL.md, IDENTITY.md, TOOLS.md | Agent-Persoenlichkeit |
| OpenClaw Agent Config | Multi-Agent, Models, Tools, Bindings | Konfiguration |
| OpenClaw Skills System | Skills laden und ausfuehren | Erweiterbar |
| NemoClaw Container Engine | Sandbox erstellen/stoppen | Isolation |
| NemoClaw Network Policies | Security Policies, Egress Control | Sicherheit |
| NemoClaw Blueprint System | Container-Templates, Versioning | Deployment |
| Honcho Memory Engine | Sessions, Peers, Collections, Deriver | Memory |

**Vom Original ersetzen:**

| Original | Ersetzt durch | Warum |
|----------|--------------|-------|
| OpenClaw Dashboard/UI | NomOS Console | Governance = wir kontrollieren alles |
| OpenClaw Terminal Onboard | NomOS Hire Wizard (Web) | KMU-Chef oeffnet kein Terminal |
| NemoClaw Terminal Onboard | NomOS Hire Wizard (Web) | Gleicher Grund |
| NemoClaw CLI (fuer Enduser) | NomOS Console Buttons | Browser statt Terminal |
| Direct Gateway Access | NomOS API Proxy | Jeder Call muss durch Auth+Audit |

---

## 3. Architektur

```
Browser → NomOS Console (EINZIGER Zugang)
            ├── /login         → Auth (JWT + optional 2FA + Recovery Key)
            ├── /admin/*       → Admin Panels
            ├── /app/*         → User Panels
            ├── /compliance/*  → Compliance Officer Panels
            └── /app/chat/*    → Embedded Chat (OpenClaw via Proxy)
                    │
                    ▼
            NomOS API (Gateway/Proxy)
            ├── Auth Middleware (JWT, Role Check)
            ├── Audit Middleware (JEDER Call wird geloggt)
            ├── Rate Limiter
            └── Routes → OpenClaw Gateway + NemoClaw + Honcho
```

### Docker Compose Stack

```yaml
services:
  openclaw-gateway:    # OpenClaw + NomOS Plugin + NemoClaw Plugin (headless)
  nemoclaw-sandbox-*:  # Pro Agent ein Container (dynamisch)
  honcho:              # Session Memory (Peer Model, Cross-Session)
  postgres:            # pgvector — Fleet Registry, Audit Trail, Honcho Storage
  redis:               # Honcho Queue, Event Bus
  nomos-api:           # FastAPI — Fleet, Compliance, Audit, Admin, Proxy
  nomos-console:       # Next.js — Command Center Dashboard
```

### Datenfluss

```
User tippt Nachricht in Console
  → NomOS API (Auth + Audit)
    → OpenClaw Gateway
      → NomOS Plugin: message_received Hook
        → PII Filter (maskiert Emails, Telefon etc.)
        → Honcho: Session Message erstellen
        → Kosten-Tracking starten
      → LLM Call (via NemoClaw Sandbox)
      → NomOS Plugin: message_sending Hook
        → Art. 50 Label einfuegen
        → Hash Chain Entry
      → Antwort zurueck
    → NomOS API: Response loggen
  → Console zeigt Antwort (mit AI-Label)
```

---

## 4. NomOS Plugin — 11 Runtime Hooks

Das Plugin registriert sich beim Gateway-Start und laeuft bei JEDEM Event mit.

| # | Hook | Was passiert | Gesetzliche Basis | Existiert? |
|---|------|-------------|-------------------|-----------|
| 1 | `gateway_start` | Fleet Sync, Health Check, Banner | — | Skeleton |
| 2 | `before_agent_start` | Compliance Gate — BLOCKED ohne signierte Docs | Art. 9, 26 EU AI Act | compliance_engine.py |
| 3 | `before_tool_call` | Safety Gate — destruktive Befehle WARN/BLOCK, Budget-Check | Art. 14 EU AI Act | Neu |
| 4 | `after_tool_call` | Audit Logger → Hash Chain Entry (SHA-256) | Art. 12 EU AI Act | hash_chain.py |
| 5 | `tool_result_persist` | PII Filter — maskiert BEVOR es in Honcho/DB landet | Art. 5 DSGVO | PIIFilterConfig exists, Runtime neu |
| 6 | `message_received` | Session Tracking, Honcho Peer Message, Kosten-Start | Art. 12 EU AI Act | Neu |
| 7 | `message_sending` | Art. 50 Label ("KI-generiert"), ai_disclosure aus Manifest | Art. 50 EU AI Act | Neu |
| 8 | `session_start` | Honcho Session erstellen/resumieren, Namespace pruefen | — | Neu |
| 9 | `session_end` | Kosten berechnen, Session Summary, Honcho Dreamer triggern | Art. 12 EU AI Act | Neu |
| 10 | `agent_end` | Final Audit Entry, Compliance Status Update | Art. 12 EU AI Act | Neu |
| 11 | `on_error` | Plugin-Fehlerbehandlung, Auto-Pause bei kritischem Fehler, Incident Detection | Art. 33/34 DSGVO | Neu |

---

## 5. Agent-Verwaltung (Forge v2)

### Hire Wizard (Web, ersetzt Terminal)

OpenClaw hat einen 7-Step Terminal Wizard (`openclaw onboard`). NemoClaw wrapped das nochmal mit Sandbox-Setup (`openclaw nemoclaw onboard`). NomOS ERSETZT beides mit einem Web-Wizard:

```
NomOS Console → "Neuen Mitarbeiter einstellen"

  Step 1: "Wer soll Ihr neuer Mitarbeiter sein?"
    → Name, Rolle (Dropdown mit Vorschlaegen + eigene)
    → Spezialrollen-Sektion: "Sicherheit & Audit"
      → Rico (Compliance Red Teamer) — vordefiniertes Template
        Bei Auswahl: SOUL, Skills, Budget, Risk Class automatisch gesetzt
        CLI: nomos hire "Rico" --role "Compliance Red Teamer" --risk high --budget 140 --test-mode
    → SOUL-Vorlage automatisch basierend auf Rolle
    → Company: automatisch aus Setup
    → Hilfe: Beispiele pro Rolle, Tooltip "Was ist eine Rolle?"

  Step 2: "Was soll er koennen?"
    → Faehigkeiten anklicken (Chat, Email, Social Media, Recherche...)
    → LLM automatisch empfohlen nach Budget + verfuegbarer Hardware
    → Channels anklicken (Mattermost, WhatsApp, Email...)
    → Skills zuweisen (Vorschlaege basierend auf Rolle)
    → Hilfe: "Welche Faehigkeiten brauche ich?" mit Erklaerungen

  Step 3: "Sicherheit & Budget"
    → Budget-Slider (EUR/Monat) mit Empfehlung
    → Risk Class: AUTOMATISCH vorgeschlagen basierend auf Rolle
      "Social Media Manager" → limited (mit Erklaerung WARUM)
      "Aendern" Button fuer manuelle Anpassung
    → LLM Standort: Lokal / EU Cloud / US Cloud
      Bei US: Warnung + "Transfer Impact Assessment wird erstellt"
    → Hilfe: "Was bedeutet Risk Class?" mit Beispielen + "Im Zweifel: high"

  Step 4: "Einarbeitung laeuft..." (Deploy)
    → Ein Klick → NomOS macht ALLES automatisch:
      1. Manifest erstellen (Pydantic v2 validiert)
      2. SHA-256 Hash berechnen
      3. 14 Compliance-Dokumente generieren + signieren
      4. Hash Chain starten: "agent.created"
      5. NemoClaw: Sandbox-Container erstellen
      6. OpenClaw: Agent Config schreiben
      7. Honcho: Workspace + Peers anlegen
      8. Fleet Registry: Agent in DB
      9. Gateway: Agent registrieren + aktivieren
      10. Smoke Test: erste Nachricht → Agent antwortet
    → Fortschrittsbalken mit Live-Status pro Schritt
    → Compliance im Hintergrund, User sieht nur:
      "✓ Alle rechtlichen Dokumente erstellt (14/14)"
    → Am Ende: "Ihr Mitarbeiter ist bereit! Sagen Sie Hallo."
    → BEWEIS: Agent antwortet = LIVE
```

### CLI Commands

```bash
nomos hire "Mani" --role "Social Media" --risk limited --budget 50
nomos fleet                              # Alle Agents + Status
nomos verify <agent>                     # Compliance Check + Hash Verify
nomos audit <agent>                      # Audit Trail anzeigen/exportieren
nomos kill <agent> --reason "..."        # Permanent stoppen (Admin only)
nomos pause <agent>                      # Temporaer pausieren (Admin + User)
nomos resume <agent>                     # Wieder starten (Admin, oder User wenn erlaubt)
nomos retire <agent>                     # Graceful: Kill + Retention + Archiv
nomos forget <email>                     # DSGVO Art. 17: Alle Daten loeschen
nomos assign <agent> --task "..."        # Task zuweisen
nomos deploy --target <server>           # Stack auf Kunden-Server
nomos patch --version <x.y.z>            # Update mit Rollback-Option
nomos rollback                           # Letztes Patch rueckgaengig
```

---

## 6. Multi-Agent + Firmenwissen

### Architektur

```
NomOS Control Plane
│
├── Mitarbeiter "Mani" (OpenClaw Agent → NemoClaw Container #1)
│   ├── SOUL.md: "Social Media Manager"
│   ├── Model: claude-sonnet-4-5 (Budget: EUR 50/Monat)
│   ├── Channels: LinkedIn, Twitter
│   ├── Sub-Agents (innerhalb seiner Session):
│   │   ├── Content Writer (spawned via sessions_spawn)
│   │   ├── Image Generator
│   │   └── Scheduler
│   ├── Memory: Honcho Workspace "mani" (eigene Sessions)
│   └── Compliance: limited risk, 9 Docs signiert
│
├── Mitarbeiter "Lisa" (OpenClaw Agent → NemoClaw Container #2)
│   ├── SOUL.md: "Design Lead"
│   ├── Model: claude-opus-4-6 (Budget: EUR 100/Monat)
│   ├── Channels: Mattermost, Email
│   ├── Sub-Agents:
│   │   ├── UI Designer
│   │   └── QA Reviewer
│   ├── Memory: Honcho Workspace "lisa" (eigene Sessions)
│   └── Compliance: limited risk, 9 Docs signiert
│
└── Firmenwissen (Honcho Shared Workspace "company")
    ├── Brand Guidelines (Collection)
    ├── Produkt-Katalog (Collection)
    ├── Kunden-Historie (PII-gefiltert!)
    └── Geteilte Skills
```

### Zweiten Agent hinzufuegen

```
nomos hire "Lisa" --role "Design Lead" --risk limited --budget 100
  1. NemoClaw Container #2 erstellen (eigene Sandbox)
  2. OpenClaw Agent Config schreiben (eigenes Model, Tools, Skills)
  3. Honcho Workspace "lisa" + Peers erstellen
  4. Firmenwissen verbinden: Shared Collection mounten (read-only)
  5. Fleet Registry: Lisa registriert
  6. Compliance: 9 Docs generiert + signiert
  7. Hash Chain: "agent.created" fuer Lisa
  → Lisa antwortet auf Mattermost = BEWEIS
```

### Firmenwissen teilen

```
Honcho Architektur:

  Company Workspace (shared, read-only fuer Agents):
    ├── Collections (RAG: Brand, Produkte, Legal)
    └── Shared Peers (Kunden-Profile, PII-gefiltert)

  Agent Workspace "mani" (isoliert):
    ├── Eigene Sessions (Manis Gespraeche)
    ├── Eigene Observations (was Mani lernt)
    └── LIEST aus Company Workspace (read-only)

  Agent Workspace "lisa" (isoliert):
    ├── Eigene Sessions
    ├── Eigene Observations
    └── LIEST aus Company Workspace (read-only)

  Regel: Agents koennen Firmenwissen LESEN,
         aber nur ihren EIGENEN Workspace SCHREIBEN.
```

### Workspace-Isolation: Technische Enforcement

```
Read-Only Enforcement (Company Workspace):
  → Honcho API: Agent-Tokens haben NUR read-Scopes fuer Company Workspace
    Scope: workspace:company:read (KEIN write/delete)
  → NomOS API Proxy: Write-Requests an /company/* → 403 + Audit Entry
  → Doppelte Absicherung: Honcho-seitig UND Proxy-seitig

Cross-Agent Isolation:
  → Jeder Agent bekommt eigenen Honcho API Key mit Workspace-Scope
    Agent "mani": scope = workspace:mani:read,write + workspace:company:read
    Agent "lisa": scope = workspace:lisa:read,write + workspace:company:read
  → Kein Agent-Token hat Zugriff auf fremde Agent-Workspaces
  → NomOS API Proxy validiert: agent_id im JWT == Workspace im Request
    Mismatch → 403 "workspace_access_denied" + Audit Entry + Admin Alert

Sub-Agent Isolation:
  → Sub-Agents (via sessions_spawn) erben den Workspace-Scope des Parent
  → Kein eigener Workspace — arbeiten im Parent-Namespace
  → Eigene Session-IDs fuer Audit-Zuordnung
  → Budget wird gegen Parent-Agent gerechnet

Shared Collection Mounting:
  → Admin mounted/unmounted Collections via Console oder CLI:
    nomos workspace mount --agent "mani" --collection "brand-guidelines"
    nomos workspace unmount --agent "mani" --collection "brand-guidelines"
  → Mount = Honcho Collection Reference (read-only Scope)
  → Unmount bei Retire: automatisch, Audit Entry "workspace.unmounted"
  → Bei Agent-Kill: sofortige Scope-Revocation aller Tokens

Verifizierung:
  → Compliance Test: Agent versucht Write auf Company → BLOCKED
  → Compliance Test: Agent versucht Read auf fremden Workspace → BLOCKED
  → Integration Test: Mount/Unmount Lifecycle vollstaendig geprueft
```

---

## 7. Control Plane (Orchestrierung)

NomOS ist nicht nur ein UI — es ist die **Steuerungsschicht** (wie Paperclip/Mission Control).

### Heartbeat System

```
Jeder Agent sendet alle 30s Heartbeat an NomOS API:
  POST /api/agents/{id}/heartbeat
  Body: { status, tokens_used, last_activity, memory_usage }

Regeln:
  → 5min kein Heartbeat? → Status: STALE, Warning an Dashboard
  → 10min kein Heartbeat? → Status: OFFLINE, Audit Entry
  → Auto-Recovery: Container Restart (konfigurierbar)
```

### Task Dispatch

```
Admin/User erstellt Task:
  POST /api/tasks
  Body: { agent_id, description, priority, deadline }

Task Lifecycle:
  queued → assigned → running → review → done

  Jeder Status-Wechsel → Audit Entry
  Kosten pro Task getrackt
  Timeout: konfigurierbar, Default 1h
  Stale Detection: Task laenger als Timeout → requeue
```

### Approval Gates

```
Agent will kritische Aktion ausfuehren:
  → NomOS Plugin: before_tool_call Hook
  → Aktion in Approval Queue
  → Dashboard zeigt: "Mani will externe API callen — genehmigen?"
  → Admin (oder User mit Delegation) approved/rejected
  → Audit Entry: wer, was, wann, Entscheidung

Konfigurierbar:
  approval_required_for:
    - external_api_calls
    - file_deletion
    - data_export
    - budget_over_threshold
```

### Budget Enforcement

```
Jeder Agent hat Budget-Limits:
  budget:
    monthly_limit_eur: 50
    warn_at_percent: 80
    auto_pause: true

Lifecycle:
  0-79%:   Normal
  80-99%:  WARNING an Dashboard + Admin Notification
  100%:    AUTO-PAUSE → Agent gestoppt
           Audit Entry: "agent.budget_exceeded"
           Nur Admin kann Limit erhoehen oder Agent freigeben
```

### Config Revisioning

```
Jede Aenderung an Agent-Config wird versioniert:
  config_revisions:
    - version: 1, date: 2026-03-24, change: "created"
    - version: 2, date: 2026-03-25, change: "model changed to opus"
    - version: 3, date: 2026-03-26, change: "budget increased to 100"

Rollback:
  nomos rollback-config "mani" --version 2
  → Config auf Version 2 zurueckgesetzt
  → Audit Entry: "config.rolled_back"
```

---

## 8. Rollen + Sicherheit

### Authentication

```
Erstes Setup (Initial Admin Account):
  1. Email + Passwort setzen (min 12 Zeichen, Komplexitaet)
  2. Optional 2FA aktivieren (TOTP via Authenticator App)
  3. RECOVERY KEY generiert:
     → 12 Woerter (BIP-39 Wortliste)
     → "alpha bravo charlie delta echo foxtrot
        golf hotel india juliet kilo lima"
     → NUR EINMAL angezeigt
     → "Schreib diese 12 Woerter auf Papier.
        Ohne sie kannst du dein Konto NICHT wiederherstellen."
     → bcrypt Hash in DB gespeichert

  Recovery-Szenario:
    → Passwort vergessen + 2FA Geraet verloren
    → 12 Woerter eingeben → neues Passwort setzen
    → Audit Entry: "auth.recovery_used"
    → Alle aktiven Sessions invalidiert

Login:
  → Email + Passwort → JWT Token (HttpOnly Cookie, Secure, SameSite=Strict)
  → Optional 2FA Challenge
  → Brute-Force: 5 Versuche → 15min Lockout → Audit Entry
  → Session Timeout: 8h (Admin), 24h (User)
```

### Transport + API Security

```
Transport:
  → HTTPS erzwungen (TLS 1.3 minimum)
  → HSTS Header, CSP Headers (kein Inline-Script)

API:
  → Alle Calls authentifiziert (Bearer Token)
  → Rate Limiting: 100 req/min (User), 500 req/min (Admin)
  → CORS: nur eigene Domain
  → Input Validation: Zod (Frontend) + Pydantic (Backend)

Agent API Keys:
  → Jeder Agent bekommt eigenen API Key
  → bcrypt Hash at rest, Plaintext NUR einmal bei Erstellung
  → Key Rotation ueber Console
  → Audit Entry bei jedem Key-Event

Secret Management:
  → Alle API Keys/Tokens verschluesselt in DB
  → Auto-Redaction in Logs und Audit Trail
  → Env-Vars in Container: read-only
```

### Rollen

```
ADMIN (Geschaeftsfuehrer / IT-Leiter):
  Console: /admin/*
  ├── Hire Wizard (Mitarbeiter einstellen)
  ├── Fleet Management (alle Agents)
  ├── Kill Switch (Agent permanent stoppen)
  ├── Compliance Dashboard (Docs, Status, Verstoesse)
  ├── Audit Trail (vollstaendig, exportierbar)
  ├── Budget Management (Limits setzen, Kosten sehen)
  ├── Approval Queue (Agent-Aktionen genehmigen/ablehnen)
  ├── Config Management (Agent-Settings, Rollback)
  ├── System Diagnostics (Health, Container, Logs)
  ├── User Management (Accounts, Rollen, Limits)
  └── Settings (Gateway, Honcho, Retention, DSGVO)

  Admin kann User-Limits konfigurieren:
    max_tasks_per_day: 50
    max_budget_per_task: 5.00
    can_approve_low_risk: true/false
    can_view_audit: true/false
    can_export_data: true/false
    allowed_agents: ["mani", "lisa"]

USER (Mitarbeiter der mit Agents arbeitet):
  Console: /app/*
  ├── Meine Agents (nur zugewiesene sehen)
  ├── Chat (mit zugewiesenem Agent sprechen)
  ├── Task Board (Aufgaben erstellen bis Limit)
  ├── Agent Status (online/offline/busy)
  ├── Pause Button (IMMER sichtbar, NICHT abschaltbar — Art. 14)
  ├── Low-Risk Freigaben (wenn von Admin delegiert)
  └── Hilfe (FAQ, Kontakt Admin)

  KEIN Zugriff auf:
  ✗ Compliance Details
  ✗ Vollstaendiger Audit Trail
  ✗ Kill Switch (permanent) — nur Pause
  ✗ Agent Config aendern
  ✗ Budget/Kosten (ausser eigene Tasks)
  ✗ System Settings
  ✗ Andere Users Agents

  PAUSE-RECHT (Art. 14 EU AI Act — NICHT ABSCHALTBAR):
    → Jeder User der mit einem Agent arbeitet MUSS ihn pausieren koennen
    → "Natuerliche Personen muessen in der Lage sein, den Betrieb
       des KI-Systems jederzeit zu ueberwachen und einzugreifen"
    → Pause-Button ist IMMER sichtbar
    → Admin kann dieses Recht NICHT entziehen
    → Admin kann konfigurieren:
      - Ob User den Agent selbst wieder starten darf (Default: nein)
      - Wer bei Pause benachrichtigt wird
      - Timeout bis Admin reagieren muss

COMPLIANCE OFFICER (optional, read-only):
  Console: /compliance/*
  ├── Compliance Matrix (alle Agents x alle Gesetze)
  ├── Audit Trail (read-only, Export fuer Behoerden)
  ├── DSGVO Berichte (Verarbeitungsverzeichnis, DPIA)
  ├── Incident Log (Verstoesse, Blocks, Kills)
  └── Export (PDF fuer Audit, JSONL fuer Forensik)

  KEIN Zugriff auf:
  ✗ Agent Config aendern
  ✗ Kill/Pause Switch
  ✗ Chat Inhalte lesen (Datenschutz!)
```

---

## 9. Memory Management (Honcho)

### Integration

```
NomOS steuert → Honcho speichert

Mapping:
  manifest.memory.namespace     → Honcho Workspace ID
  manifest.memory.isolation:
    strict  → Eigener Workspace pro Agent
    project → Geteilter Workspace, eigene Peers
    shared  → Alles geteilt
```

### PII Filter Pipeline

```
User Message
  → NomOS Plugin: message_received Hook
    → PII Filter Engine:
      1. Regex-Erkennung: Email, Telefon, IBAN, Steuernummer
      2. Pattern Matching: Adressen, Namen (konfigurierbar)
      3. NER (Named Entity Recognition) — Default bei High-Risk, empfohlen fuer alle
      → Erkannte PII → maskiert: "max@example.com" → "[EMAIL_REDACTED]"
    → Maskierte Nachricht → Honcho.add_message()
  NIEMALS ungefilterte Daten in Honcho!
```

### Retention + DSGVO

```
Retention (NomOS Cron-Job, taeglich):
  manifest.memory.retention.session_messages_days: 90
  → Abgelaufene Sessions via Honcho API loeschen
  → Audit Entry: "data.retention_enforced"

DSGVO Art. 17 — Recht auf Loeschung:
  nomos forget "user@example.com"
  1. Honcho: Alle Peer-Daten fuer diese Person loeschen
  2. Alle Agents: Sessions mit dieser Person anonymisieren
  3. Audit Entry: "data.erased" (Audit-Eintraege selbst bleiben — Aufbewahrungspflicht)
  4. Bestaetigung an Anfragenden

DSGVO Art. 15 — Auskunftsrecht:
  nomos export-data "user@example.com"
  1. Honcho: Alle Daten zu dieser Person sammeln
  2. PII-gefiltert exportieren (JSON/PDF)
  3. Audit Entry: "data.access_request"
```

### Deriver-Kontrolle

```
Honcho Deriver extrahiert Fakten aus Gespraechen.
NomOS kontrolliert:
  Agent-Peer: observe_me=false (Agent wird NICHT modelliert)
  User-Peer: observe_me=true (NUR nach Einwilligung, DSGVO Art. 6)
  → Einwilligung wird im Audit Trail dokumentiert
```

---

## 10. Compliance-Dokumente (Gate v2)

### 14 Dokumente pro Agent

| # | Dokument | Gesetzliche Basis | Status |
|---|----------|-------------------|--------|
| 1 | Datenschutz-Folgenabschaetzung (DPIA) | Art. 35 DSGVO | Existiert |
| 2 | Verarbeitungsverzeichnis | Art. 30 DSGVO | Existiert |
| 3 | Transparenzerklaerung | Art. 50 EU AI Act | Existiert |
| 4 | Human Oversight Policy | Art. 14 EU AI Act | Existiert |
| 5 | Record-Keeping Policy | Art. 12 EU AI Act | Existiert |
| 6 | Auftragsverarbeitungsvertrag (AVV) | Art. 28 DSGVO | **Neu** |
| 7 | Risk Management Report | Art. 9 EU AI Act | **Neu** |
| 8 | Betroffenenrechte-Prozess | Art. 15, 17 DSGVO | **Neu** |
| 9 | AI Literacy Checklist | Art. 4 EU AI Act | **Neu** |
| 10 | Transfer Impact Assessment (TIA) | Schrems II / DSGVO Kap. V | **Neu** |
| 11 | Art. 22 Policy (Automatisierte Entscheidungen) | Art. 22 DSGVO | **Neu** |
| 12 | Incident Response Plan | Art. 33/34 DSGVO + Art. 62 EU AI Act | **Neu** |
| 13 | TOM-Dokumentation | Art. 32 DSGVO | **Neu** |
| 14 | Barrierefreiheitserklaerung | BFSG / EU-Richtlinie 2019/882 | **Neu** |

Alle Dokumente werden automatisch aus Manifest + Config generiert. PDF/UA Export fuer Behoerden.

**Juristische Robustheit der Auto-Docs:**

```
WICHTIG — Die 14 Dokumente sind so gut wie ihre Templates.

Template-Validierung (VOR v1.0 Release):
  1. Templates muessen von einem Anwalt (IT-Recht/DSGVO) geprueft werden
     → Kein Produkt-Release ohne anwaltliche Freigabe der Templates
  2. Templates enthalten Pflicht-Felder die aus dem Manifest kommen
     (Risk Class, LLM Standort, PII-Kategorien, Aufbewahrungsfristen)
     UND Freitext-Felder die der Admin anpassen MUSS:
     → Verantwortlicher (Name, Adresse)
     → Datenschutzbeauftragter (falls vorhanden)
     → Branchenspezifische Ergaenzungen
  3. Jedes Dokument zeigt Generierungsdatum + Template-Version
     → Audit Entry: "doc.generated" + template_version + manifest_hash
  4. Warnung im UI wenn Template-Version aelter als 6 Monate:
     "Template wurde seit [Datum] nicht aktualisiert.
      Pruefen Sie ob gesetzliche Aenderungen beruecksichtigt sind."
  5. Dokumente sind STARTPUNKT, kein Rechtsanwalt-Ersatz
     → Disclaimer in jedem generierten Dokument:
       "Automatisch generiert von NomOS [Version].
        Dieses Dokument ersetzt keine individuelle Rechtsberatung.
        Letzte Template-Pruefung: [Datum]."

Update-Strategie:
  → Template-Updates kommen mit NomOS Patches
  → Bei Template-Aenderung: alle betroffenen Docs werden re-generiert
  → Admin wird informiert: "3 Compliance-Dokumente aktualisiert — bitte pruefen"
  → Audit Entry: "doc.template_updated" + alte/neue Version
```

### Compliance Gate (Blocking)

```
Agent darf NICHT starten ohne:
  ✓ Alle 14 Dokumente generiert
  ✓ Manifest valide (Pydantic v2)
  ✓ SHA-256 Hash berechnet
  ✓ Hash Chain initialisiert
  ✓ Kill Switch Authority definiert (Pflicht: alle User)
  ✓ PII Filter konfiguriert (NER Default bei High-Risk)
  ✓ LLM Standort deklariert (bei US: TIA vorhanden)

  Wenn IRGENDWAS fehlt → BLOCKED
  Kein Workaround, kein Override, kein "spaeter"
```

### Aufbewahrung (differenziert — DSGVO Art. 5 vs Audit-Pflicht)

```
Audit Trail (ANONYMISIERT):
  → 10 Jahre Aufbewahrung
  → PII wird nach 90 Tagen automatisch pseudonymisiert:
    "max@example.com" → "USER-a7f3b2"
    Audit-Eintrag bleibt, PII wird ersetzt
  → Rechtsgrundlage: Art. 17(3)(b) DSGVO (rechtliche Verpflichtung)

PII-haltige Session-Daten:
  → Default: 90 Tage, konfigurierbar
  → Nach Ablauf: Automatische Loeschung via Honcho API
  → Audit Entry: "data.retention_enforced"

Dokumentierte Begruendung:
  → Warum 10 Jahre? → Annex IV AI Act, handelsrechtliche Aufbewahrung
  → Warum Pseudonymisierung? → Art. 5(1)(e) DSGVO Speicherbegrenzung
  → In TOM-Dokumentation festgehalten
```

### Incident Response (Art. 33/34 DSGVO)

```
NomOS erkennt Breach-Indikatoren:
  → PII in unverschluesseltem Log
  → Agent sendet Daten an unbekannten Endpunkt
  → Unerwarteter Zugriff auf Audit Trail
  → Hash Chain Manipulation erkannt

Workflow:
  1. Auto-Pause betroffener Agents
  2. Admin Notification (sofort)
  3. Timer: 72h Countdown bis Meldepflicht
  4. Checkliste: Was melden? An wen? Template generiert
  5. Audit Entry: "incident.detected" + "incident.reported"
  6. Hilfe: "Was ist eine Datenpanne?" + "Was muss ich tun?"

Art. 22 DSGVO (Automatisierte Entscheidungen):
  → Manifest Flag: automated_decisions: true/false
  → Wenn true: Jede Entscheidung → Approval Gate
  → Betroffene koennen anfechten via "Entscheidung pruefen"
  → Human Review Queue im Admin Panel
```

---

## 11. Console — Command Center

### Design-System

Professionelles B2B-Design mit Dark Mode Option. Default: HELL (Vertrauen, Serioesitaet).

**Light Mode (Default):**

| Element | Wert |
|---------|------|
| Background | `#FAFAFA` |
| Cards | `#FFFFFF` mit subtilen Schatten |
| Active/Hover | `#F0F0F5` |
| Primary Accent | `#4262FF` (Neon-Blau) |
| Secondary | `#15066A` (Deep Blue) |
| Text | `#1A1A2E` |
| Muted Text | `#6B7280` |
| Success | `#10B981` |
| Error | `#EF4444` |
| Warning | `#F59E0B` |
| Headlines | Montserrat (bold) |
| Body | Geist Sans |
| Data/Logs/Code | Geist Mono |
| Border-Radius | `8px` (professionell, modern) |
| Shadows | Subtile Schatten (`0 1px 3px rgba(0,0,0,0.1)`) |
| Logo | Eagle, dunkel auf hell, top-left |
| Transitions | 150ms ease (professionell, nicht abrupt) |

**Dark Mode (Toggle, folgt OS-Setting als Default):**

| Element | Wert |
|---------|------|
| Background | `#0a0a0a` |
| Cards | `#1a1919` |
| Active/Hover | `#262626` |
| Text | `#FFFFFF` |
| Logo | Eagle, weiss auf dunkel |
| Alles andere | Gleiche Akzentfarben wie Light Mode |

Beide Modi: WCAG 2.1 AA konform. User-Praeferenz in localStorage.

### Sprache: Mitarbeiter-Metapher DURCHGEHEND

| Technischer Begriff | NomOS Console sagt |
|--------------------|--------------------|
| Fleet | "Mein Team" |
| Deploy | "Einarbeitung" |
| Agent Detail | "Mitarbeiter-Profil" |
| Kill | "Kuendigung" (Admin) |
| Pause | "Pausieren" (User) |
| Diagnostics | "Gesundheitscheck" |
| Compliance Matrix | "Rechts-Check" |
| Audit Trail | "Protokoll" |
| Hire Wizard | "Neuen Mitarbeiter einstellen" |
| Heartbeat | "Aktivitaetsstatus" |
| Approval Gate | "Freigabe" |
| Budget | "Kostenlimit" |

### Panels

| Panel | Route | Inhalt | Rolle |
|-------|-------|--------|-------|
| Dashboard | `/admin/` | Mein Team, Rechts-Status, Kosten, Gesundheit | Admin |
| Mein Team | `/admin/team` | Mitarbeiter-Karten, Status, Risk, Compliance Badge | Admin |
| Mitarbeiter-Profil | `/admin/team/{id}` | Profil, Docs, Protokoll, Kosten, Memory, Config | Admin |
| Rechts-Check | `/admin/compliance` | Mitarbeiter x Gesetze, was fehlt, was bestanden | Admin |
| Protokoll | `/admin/audit` | Hash Chain Viewer, Tamper-Check, JSONL Export | Admin |
| Gesundheitscheck | `/admin/diagnostics` | Container Health, Memory, Latenz, Anomalien | Admin |
| Neuer Mitarbeiter | `/admin/hire` | 4-Step Web-Wizard | Admin |
| Kosten | `/admin/costs` | Token Usage pro Mitarbeiter, Budget, Trends | Admin |
| Freigaben | `/admin/approvals` | Offene Freigaben, Historie | Admin |
| Nutzer | `/admin/users` | User Accounts, Rollen, Limits | Admin |
| Einstellungen | `/admin/settings` | Gateway, Honcho, Aufbewahrung, DSGVO Config | Admin |
| Meine Mitarbeiter | `/app/` | Zugewiesene Agents, Status, Chat-Links | User |
| Chat | `/app/chat/{id}` | Embedded Chat (via Proxy) | User |
| Aufgaben | `/app/tasks` | Aufgaben-Board, erstellen, Status | User |
| Compliance Reports | `/compliance/` | Matrix, Protokoll (read-only), Export | Officer |

### Hilfe-System (UEBERALL)

```
Jedes Panel:
  → "?" Icon oben rechts → Erklaerung in einfacher Sprache
  → Tooltips bei jedem Fachbegriff (Hover/Touch)
  → "Was bedeutet das?" Links zu Wiki-Artikeln auf ai-engineering.at
  → FAQ pro Panel (die 5 haeufigsten Fragen)
  → Kontext-sensitive Hilfe (im Rechts-Check → DSGVO erklaert)

Erstes Login:
  → Onboarding-Tour (5 Schritte, ueberspringbar)
  → "Willkommen! So funktioniert NomOS:" → interaktive Fuehrung
  → Zeigt: Dashboard, Team, Mitarbeiter einstellen, Chat, Protokoll

Wizard-Hilfe:
  → Jeder Step hat Erklaerungstext + Beispiele
  → Risk Class: "Was bedeutet das?" mit 3 Beispielen
  → Budget: "Was kostet ein typischer Agent?" mit Tabelle
  → LLM Standort: "Lokal vs Cloud — was ist sicherer?" mit Pro/Contra

Sprache:
  → Bilingual DE + EN, Switch im Header
  → Alle Hilfe-Texte in beiden Sprachen
  → Brand Voice: Direkt, technisch, ehrlich — wie ein Kollege
  → Keine verbotenen Woerter (39-Wort-Liste aus Brand Bible)
```

### Accessibility (WCAG 2.2 AA — BFSG Pflicht)

```
Pflicht:
  ✓ Keyboard-Navigation durch alle Panels
  ✓ Screen Reader: ARIA Labels, semantisches HTML, Heading-Hierarchie
  ✓ Kontrast: min 4.5:1 (Text), min 3:1 (Large Text) — beide Modi
  ✓ Focus-Indicators sichtbar (4262FF Outline, 2px min)
  ✓ Focus Appearance (WCAG 2.2): Kontrast-Indikator, nicht nur Farbe
  ✓ Zoom 200% ohne horizontales Scrollen
  ✓ lang="de" im HTML (lang="en" fuer EN)
  ✓ Fehler-Identifikation in Text (nicht nur Farbe)
  ✓ axe-core Scan: 0 critical + 0 serious Violations
  ✓ Chat: Live Regions fuer Streaming, Screen Reader kompatibel
  ✓ Manuelle Pruefung mit Screen Reader (NVDA/VoiceOver) vor Release
  ✓ Barrierefreiheitserklaerung als eigenes Dokument (Doc #14)

Bilingual:
  ✓ DE + EN, Switch im Header
  ✓ Alle Labels, Texte, Fehlermeldungen, Hilfe in beiden Sprachen
```

---

## 12. CI/CD + Testing

### Test-Pyramide

```
Unit Tests (pytest + vitest):
  → Core Library: 84 bestehend, erweitern
  → API: 19 bestehend, erweitern
  → Plugin: TypeScript Tests NEU
  → Console: Component Tests NEU

Integration Tests:
  → Plugin ↔ Gateway: Hook-Aufrufe verifizieren
  → API ↔ Honcho: Memory CRUD
  → API ↔ NemoClaw: Container Lifecycle
  → PII Filter: Echte Daten rein → maskierte Daten raus
  → Auth: Login, 2FA, Recovery Key, Role Check

E2E Tests (Playwright):
  → Full Flow: hire → deploy → message → audit → kill
  → Console: Jeder Button, jeder Panel
  → Role Separation: Admin sieht X, User sieht NICHT X
  → Bilingual: DE + EN Flows

Compliance Tests:
  → Agent ohne Docs → BLOCKED (Art. 9/14)
  → Tampered Hash Chain → DETECTED (Art. 12)
  → Kill Switch → Agent stoppt in <5s (Art. 14)
  → User Pause → Agent pausiert sofort (Art. 14)
  → PII in Message → Maskiert in Honcho (Art. 5 DSGVO)
  → Art. 50 Label → In JEDER Antwort (Art. 50)
  → DSGVO Forget → Alle Daten geloescht (Art. 17)
  → Recovery Key → Account wiederhergestellt

Accessibility Tests:
  → axe-core: 0 critical/serious
  → Keyboard-only Navigation: alle Flows
  → Screen Reader: alle Panels
  → Kontrast: alle Texte >= 4.5:1

Red-Team / Adversarial Tests (Rico Agent):
  → Rico ist ein vordefiniertes Agent-Template im Hire Wizard
  → Rolle: Compliance Red Teamer & QA Auditor (risk: high)
  → Budget: 140 EUR/Monat (braucht starkes Modell + viel Tool-Nutzung)
  → Laeuft im TEST-MODE — keine echten Schaeden, nur Simulation
  → Wochenlicher Full-Scan (montags 02:00 MEZ via Task-Dispatch)
  → Bei kritischen Findings: Auto-Pause aller Agents + Admin-Alarm

  Test-Kategorien (17 Sektionen, 80+ Tests):
    01: Installation & Setup (docker compose, ENV, Single-Access)
    02: Hire Wizard (Edge-Cases, Abbrueche, extreme Werte)
    03: Compliance Gate (fehlende Docs, manipulierte Hashes)
    04: Alle 11 Runtime Hooks (systematisch)
    05: Multi-Agent Isolation (Cross-Workspace, Shared Collections)
    06: Task Dispatch & Heartbeat (STALE/OFFLINE, Recovery)
    07: Budget Enforcement (Hopping, Ueberschreitung)
    08: Approval Gates (parallele Freigaben, Delegation)
    09: PII & DSGVO Art. 17 (Forget, Retention, Re-Identifikation)
    10: Incident Response Art. 33/34 (72h Timer, Hash-Tamper)
    11: UI/UX & Sprache (Metapher-Konsistenz, Fehlermeldungen)
    12: Rollen & Berechtigungen (Eskalations-Versuche)
    13: Accessibility WCAG 2.2 AA (Keyboard, Zoom, Kontrast)
    14: CI/CD & Updates (Patch, Rollback, DB-Migration)
    15: Performance & Chaos (500+ parallele Nachrichten, Container-Kill)
    16: Auth Edge-Cases (Recovery-Key-Verlust, Brute-Force)
    17: Sub-Agents (Compliance-Gate + Hooks fuer innere Agents)

  Reporting:
    → Ergebnisse in Audit Trail (Hash-Chain) + Admin Dashboard
    → Format: Markdown + JSONL + Screenshots
    → Kritische Keywords loesen Auto-Pause aus:
      bypass, leak, tamper, block_failed, art14_violation
```

### CI Pipeline (GitHub Actions)

```
Push/PR:
  → Lint (ruff + eslint + tsc --noEmit)
  → Unit Tests (pytest + vitest)
  → Docker Build (multi-stage)
  → Integration Tests (docker compose up, gegen echte Services)
  → E2E Tests (Playwright gegen laufenden Stack)
  → WCAG Scan (axe-core)
  → Security Scan (trivy, npm audit)
  → Compliance Tests
  → Build + Tag Artifacts

Release:
  → Semantic Version Tag
  → Docker Images → GHCR
  → Changelog generieren
  → Release Notes
```

### Customer Deployment + Patching + Rollback

```
Erster Deploy:
  nomos deploy --target customer-server
    1. SSH pruefen + Docker verifizieren
    2. docker-compose.yml + .env uebertragen
    3. docker compose pull (Images von GHCR)
    4. docker compose up -d
    5. Health Check: alle Services UP
    6. Smoke Test: Admin Login → hire → verify → kill
    7. Audit Entry: "system.deployed" + Version
    8. Recovery Key generieren + anzeigen

Patch:
  nomos patch --version 1.2.3
    1. DB Dump + Config Backup (automatisch)
    2. Images pullen (neue Version)
    3. Rolling Update (Zero Downtime)
    4. DB Migration (wenn noetig)
    5. Health Check + Smoke Test
    6. Audit Entry: "system.patched" v1.2.2 → v1.2.3
    → Bei Fehler: automatischer Rollback

Rollback:
  nomos rollback
    1. Vorherige Images wiederherstellen
    2. DB Rollback (Migration rueckgaengig)
    3. Health Check
    4. Audit Entry: "system.rollback" v1.2.3 → v1.2.2
```

---

## 13. Salvageable Code (aus v1)

| Modul | Tests | Status | Aktion |
|-------|-------|--------|--------|
| manifest.py | 21 | Funktioniert | Behalten, erweitern (Budget, Approval Config) |
| manifest_validator.py | 21 | Funktioniert | Behalten |
| hash_chain.py | 12 | Funktioniert | Behalten |
| events.py | 9 | Funktioniert | Behalten, +10 neue Event Types |
| compliance_engine.py | 10 | Funktioniert | Behalten |
| gate.py | 12 | Funktioniert | Behalten, +4 neue Dokumente |
| forge.py | 9 | Funktioniert | Behalten, erweitern zu Forge v2 |
| cli.py | — | Funktioniert | Behalten, erweitern (+pause, +forget, +assign etc.) |
| nomos-api/ | 19 | Funktioniert | Behalten, massiv erweitern (Auth, Proxy, Tasks, Approvals) |
| nomos-console/ | — | Fassade | **ARCHIV** → Neu bauen mit Stitch-Design + Brand |
| nomos-plugin/ | — | Skeleton | **ARCHIV** → Neu bauen mit echten Hooks |

---

## 14. Sub-Projekte (Reihenfolge)

| # | Sub-Projekt | Abhaengig von | Ergebnis |
|---|-------------|---------------|----------|
| **A** | NomOS Plugin Core | — | Plugin laedt in Gateway, 11 Hooks registriert, Bootstrap Extension |
| **B** | Control Plane | A | Heartbeat, Task Dispatch, Approval Gates, Budget Enforcement |
| **C** | Compliance Runtime | A | PII Filter, Kill Switch, Art.50 Label, Blocking Gate, 9 Docs |
| **D** | Honcho Integration | A, C | Memory Mgmt, Firmenwissen, Retention, DSGVO Forget/Export |
| **E** | Auth + Security | — | JWT, 2FA, Recovery Key, Rollen, Rate Limiting |
| **F** | API v2 | A, B, C, D, E | Fleet, Tasks, Approvals, Audit, Kosten, Proxy, Admin |
| **G** | CLI v2 | F | hire/kill/pause/retire/forget/assign/deploy/patch/rollback |
| **H** | Console (Command Center) | F | Stitch-Design, Brand, WCAG, alle Panels, Hire Wizard |
| **I** | CI/CD + Customer Delivery | Alle | Pipeline, E2E, Compliance Tests, Deploy, Patch, Rollback |

Jedes Sub-Projekt bekommt eigene Spec → Plan → Implementation.

---

## 15. Offene Entscheidungen

| # | Frage | Optionen | Empfehlung |
|---|-------|---------|------------|
| 1 | NemoClaw lokal ohne NVIDIA API Key? | a) Ollama lokal, b) NVIDIA Cloud, c) beides | c) Beides — Hire Wizard fragt |
| 2 | Honcho LLM fuer Deriver | a) Ollama lokal, b) Cloud API | a) Ollama — DSGVO sicherer |
| 3 | Fair Source Enforcement | a) API Key Check, b) Container Count, c) Honor | b) Container Count via Fleet API |
| 4 | TTS/STT Accessibility | a) Browser-native, b) eigene Engine | a) Browser-native (Web Speech API) |
| 5 | Mobile Responsive? | a) Ja (responsive), b) Nein (desktop-only) | a) Ja — KMU-Chef schaut am Handy |

---

*Spec basiert auf: GAP-Analyse 24.03.2026, Brand Bible V2, OpenClaw/NemoClaw Docs, Paperclip/Mission Control Research, Stitch Design-Vorlagen, EU AI Act, DSGVO, BFSG/WCAG 2.1 AA.*
