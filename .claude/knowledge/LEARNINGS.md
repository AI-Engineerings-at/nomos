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

---

## Session 20.05 (Audit-Trail v2 + Post-Release-Audit)

### L035 — "Auth auf State-Change Endpoints" muss **ALLE** state-change endpoints umfassen, nicht nur 3
Beim Audit-Härtungs-PR #5 (Phase-A1 + Auth) wurden nur `routers/agents.py`, `routers/audit.py`, `routers/proxy.py` mit `check_agent_access` / `require_admin` versehen. **7 weitere state-change Router blieben offen**: `dsgvo.py`, `tasks.py`, `approvals.py`, `workspace.py`, `incidents.py`, `compliance.py` (gate), `budget.py` + `costs.py`. Jeder authentifizierte Tenant konnte fremde Agents manipulieren, fremde DSGVO-Löschungen triggern, fremde Approvals approven. **Mach es SO**: bei "AuthZ-Härtung" IMMER `grep -l 'router = APIRouter' nomos-api/nomos_api/routers/` durchsweepen + jede `POST|PATCH|DELETE`-Route gegen `check_agent_access`/`require_admin` prüfen. Audit-Findings darunter führen, nicht selektiv "die wichtigsten" härten.

### L036 — Version-Bump bedeutet Code + Doku + UI-Strings — nicht nur `pyproject.toml`
Bei 0.1.0 → 0.2.0 wurden `pyproject.toml` (api/cli) und `package.json` (console) gebumpt — aber NICHT `config.py:47` `api_version = "0.1.0"` (→ `/health` reportet falsch), NICHT `cli.py:64` `version_option(version="0.1.0")` (→ `nomos --version` falsch), NICHT die `console UI v0.1.0`-Strings in login.tsx + sidebar.tsx (→ User sieht falsche Version). **Mach es SO**: vor jedem Version-Bump `grep -rn "0\.1\.0" nomos-cli/ nomos-api/ nomos-console/` + jeden Treffer triagen. ODER zentralen Single-Source bauen (`__version__ = importlib.metadata.version("nomos-api")`).

### L037 — Vault-Pfade in Doku müssen Code als Single-Source-of-Truth nutzen
`vault/init-entrypoint.sh` schreibt zu `nomos/secrets/audit` (KV v2). Aber `docs/operations-runbook.md` listete **3 verschiedene Pfade**: `secrets/audit/hmac_key`, `secret/nomos/audit/hmac_key`, `secret/nomos/audit-signing/private_key_hex`. **Key-Rotation-Drill nach Doku schlägt silent fehl**. **Mach es SO**: Vault-Pfade aus dem Init-Script kopieren, nicht erfinden. Bei jedem Runbook-Update grep im Code nach dem Pfad.

### L038 — `verify_chain` muss `sequence == i` UND Genesis-`previous_hash` explizit checken
HMAC + Ed25519-Signatur verhindern Tampering pro Eintrag — **aber NICHT Prefix-Truncation** wenn der Angreifer die Schlüssel hat (z.B. via Vault-Compromise). Ein Angreifer löscht Einträge 0..N, schreibt HMACs+Sigs neu und die Chain verifiziert. Der einzige Schutz ist (a) `sequence[0] == 0` UND (b) `previous_hash[0] == "0"*64`. Bevor das gefixt ist, sind externe Anker **zwingend WORM** für non-repudiation. **Mach es SO**: jede append-only Chain MUSS Sequence-Continuity + Genesis-Boundary prüfen, nicht nur Per-Entry-Integrity.

### L039 — Rekursive Algorithmen in öffentlichen API-Endpoints sind DoS-Vektoren
`merkle._mth` + `_path` waren rekursiv mit List-Slicing. Bei 1M Einträgen: Python recursion limit (1000) Crash + O(n) memory pro recursion-Level. STH/Proof-Endpoints hatten **kein Rate-Limit**. Trivialer Auth-User-DoS. **Mach es SO**: jede Funktion die User-controlled `n` verarbeitet → iterativ implementieren ODER `n` cappen. JEDER neue Endpoint default-Rate-Limit aus `nomos-api/nomos_api/middleware/rate_limit.py` einhängen, keine Ausnahme.

### L040 — Audit-Anker dürfen NICHT in die Chain schreiben die sie verankern
`audit_anchor.py` schreibt `AUDIT_CHAIN_ANCHORED`-Marker IN die Chain die es soeben verankert hat. Folge: jeder Anker beschreibt einen `head_hash` der eine Sekunde später **bereits stale** ist (der neue Marker hat den head verschoben). Identisches Anti-Pattern bei `audit_integrity_checkpoint`. Externe Verifier sehen "Anker X, aktueller head Y" und müssen erst den Anker-Marker selbst suchen um den Unterschied zu erklären. **Mach es SO**: Anker/Checkpoint-Events in **separate** `anchors.jsonl` / `checkpoints.jsonl` schreiben, NICHT in die Agent-Event-Chain. Die Chain bleibt für Domain-Events. Forward-Marker in der Chain machen sie zu einem "moving target" — schlecht für Forensik.

### L041 — Post-Release-Audit mit mehreren Agents findet was Pre-Release-Tests übersehen
5-Agent-Audit-Pass (Security / QA / Architecture / Error-Handling / Ops) fand **102 Findings** nach einem als "v0.2.0 fertig" deklarierten Release: 17 Critical/Blocker, 32 High. Davon 7 Critical AuthZ-Lücken die in 17 Sessions Pre-Release-Tests durchrutschten. **Mach es SO**: vor JEDEM Tag-Push einen Multi-Agent-Audit-Pass laufen lassen (mind. nomos-security + nomos-qa + Explore-Error-Handling). 5-15 min Investment, spart Hotfix-Release. Tag dann mit ehrlichem Confidence-Level: "v0.2.0 — released; v0.2.0 + Audit-Pass = trustworthy".
