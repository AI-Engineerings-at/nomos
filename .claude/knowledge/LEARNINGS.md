# Erkenntnisse — NomOS

> Nutzbare Vorgaben: "Mach es SO" Format.
> Jede Erkenntnis ist eine prozedurale Handlungsanweisung.

---

## Session 27.03 (Stabilisierung v2)

### L001 — Types von API ableiten, nicht erfinden
Frontend-Types die nicht zur API passen crashen React. IMMER API starten, Response inspizieren, Types daraus ableiten.

### L002 — Nicht raten, Doku lesen
OpenClaw Endpoints, NVIDIA Model-Namen, Gateway Config — IMMER Doku lesen. Raten = Fehler.

### L003 — Kein Feature auf Fake-Fundament
8 In-Memory Services haben alles instabil gemacht. IMMER gegen echte Docker-Services entwickeln.

### L004 — Ein Feld-Mismatch = ein Crash
`title` statt `description`, `compliant` statt `passed` — JEDES falsche Feld crasht die UI.

### L005 — Rate Limiter ist Distributed
Valkey-backed, persistiert bei API-Restart. State lebt im Cache, nicht im Prozess.

### L006 — `is_active = false` unsichtbar
User deaktiviert → Login 401 ohne klare Fehlermeldung. Error Messages muessen den Grund nennen.

### L007 — Next.js rewrites sind Build-time
`NOMOS_API_URL` muss beim Build gesetzt werden, nicht beim Start.

### L008 — Windows Bind-Mounts = mode 777
OpenClaw blockiert world-writable Plugins. Dockerfile COPY mit `--chown=node:node`.

### L009 — Plugin Event-Types muessen registriert sein
audit.py validiert, unbekannte Events werden abgelehnt. IMMER EventType in events.py registrieren.

## Session 28.03 (Phase 2.1 Vitest + NSS Discovery)

### L010 — Compliance ist Architektur, nicht Feature
NomOS ist eine "Compliance Control Plane" (Design Spec). Guardian Shield, EU AI Act, GDPR sind das Produkt, nicht optional.

### L011 — Test Factory Pattern skaliert
4-state coverage factory reduzierte boilerplate von 100+ auf 13 Zeilen pro Page-Test.

### L012 — Fixtures als Kontrakt
Mock-Daten die API-Schemas matchen verhindern Type Mismatches. Fixtures = erste Linie der Defense.

### L013 — Security Audit Early
NVIDIA_API_KEY in `.env` (local, gitignored, aber real). Rotation jetzt > spaeter.

### L014 — Plan vs. Product Spec Mismatch
Plan sagte "Control Plane" aber Tests waren "UI Panel". Testplan mit Product-Definition alignen.

## Session 01.04 (Leak-Analyse + OpenClaw Update)

### L015 — Claude Code Leak: 90% irrelevant fuer NomOS
CLI Agent vs Control Plane. Nuetzlich: Schema-first bestaetigt, Hook-Blaupause (155 Files).

### L016 — OpenClaw Releases pruefen BEVOR man weiterbaut
v2026.3.22 hatte 13 Breaking Changes, Plugin Entry Point war veraltet. IMMER Image pinnen, nie `:latest`.

### L017 — definePluginEntry() ist Pflicht seit v2026.3.22
Altes `export default function register()` wird deprecated.

### L018 — Projekt Genesis: Nur paths-Frontmatter sinnvoll
Worktree-Script, Coordinator, Scratchpad, Microcompaction — alles bereits in Claude Code eingebaut.

### L019 — NACH JEDEM RENAME: grep nach dem alten Namen
`newStatus` → `action` Rename liess eine Referenz stehen → ReferenceError. IMMER `grep -r "alteName"`.

### L020 — NACH JEDER TYPE-AENDERUNG: alle Fixtures/Mocks pruefen
`vault` Feld zu HealthResponse hinzugefuegt aber mockHealth Fixture vergessen. IMMER `grep -r "TypeName"`.

### L021 — NACH JEDEM FIX: alle Tests laufen lassen SOFORT
Nicht erst am Ende. Jeder Fix → Test Run.

### L022 — Kleine Gaps = grosse Fehler
Ein vergessenes Rename, eine vergessene Fixture, ein fehlender Guard — Runtime-Crash fuer den Kunden. Null Toleranz.

## Session 02-05.04 (Production Readiness + Integration Test)

### L023 — Unit Tests und Audits ersetzen KEINEN Browser-Test
3 Audits, 2 Code Reviews, "alles aligned" — erster Browser-Test: 5 echte Failures. IMMER docker compose up + Browser BEVOR etwas als "fertig" gilt.

### L024 — Dockerfile muss ALLE Dateien kopieren
alembic/ und alembic.ini fehlten im Docker Image. JEDE neue Datei → Dockerfile pruefen.

### L025 — Hardcoded Listen im Frontend sind Gift
COMPLIANCE_DOCS hatte 14 erfundene Namen mit ZERO Match zum Backend. Listen vom Backend laden oder EXAKT synchronisieren.

### L026 — Onboarding muss Zero-Friction sein
Agent erstellt → "Nicht compliant" → keine Erklaerung → User steckt fest. Compliance-Docs automatisch generieren. kill_switch_authority automatisch setzen.

### L027 — NVIDIA API Free Tier hat Rate Limits
Chat funktioniert architektonisch, Provider blockiert bei 429. Fallback-Provider oder Error-Handling noetig.

### L028 — Gegen echte API testen, nicht gegen Schemas
Schema sagt "6 Felder", API liefert 3. Docker-Image alt. IMMER curl gegen laufende API.

### L029 — Plugin-Build wird nicht automatisch deployed
Source-Code aendern reicht nicht — `npx tsc` + Docker rebuild noetig. IMMER `docker compose build` nach Plugin-Aenderungen.

### L030 — OpenClaw v2026.3.x Scope Bug
Token Auth gibt nicht automatisch alle Scopes. Workaround: `x-openclaw-scopes` Header mitsenden. Siehe github.com/openclaw/openclaw/issues/52085.

### L031 — OpenClaw Chat Model muss "openclaw" sein
`/v1/chat/completions` erwartet `model: "openclaw"`, NICHT den Provider-Model-Namen direkt.

### L032 — OpenClaw /v1/chat/completions ist ein AGENT-LOOP, kein LLM-Proxy
Jeder Request durchlaeuft System-Prompt, Tools, Sessions, Memory. Fuer einfachen Chat: Direct-LLM-Proxy bauen der die Provider-API direkt aufruft.

### L033 — Plugin ohne API Key = stiller Totalausfall
before-agent-start Hook prueft Compliance via API. Ohne API Key: 401 → Hook injiziert "STOP" in System-Prompt → LLM verweigert Antwort. Kein Error sichtbar, nur "No reply from agent". IMMER API Key via ENV injizieren.

### L034 — Dual-Mode Proxy ist die Loesung
Direct-LLM fuer Chat (~2s, zuverlaessig). Gateway Agent-Loop fuer agentic Workflows (Tools, Approval). Beides parallel, Fallback-Kette.
