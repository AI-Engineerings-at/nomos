# NomOS Infrastructure Hardening v2 — Design Spec

> **Status:** ENTWURF v1
> **Datum:** 05.04.2026
> **Ziel:** Vault als Pflicht-Service mit Auto-Init, First-Time Setup Wizard, vollstaendige E2E Tests, Structured Logging. Keine Kompromisse.
> **Vorgaenger:** Enterprise Hardening Plan (Phase 0-2, COMPLETE), Production Polish (COMPLETE)
> **Design Spec Alignment:** Geprueft gegen `docs/superpowers/specs/2026-03-24-nomos-v2-design.md`

---

## 1. Problemstellung

NomOS funktioniert E2E (Hire → Chat → Antwort), aber die Infrastruktur hat Luecken:

- Vault ist "not_configured" — Secrets liegen in ENV statt verschluesselt
- Kein First-Time Setup Wizard — Kunde muss `.env` manuell editieren
- Kein E2E Test gegen Docker Stack — 5 Failures beim ersten echten Browser-Test
- Kein Structured Logging — Debugging nur mit `docker logs | grep`
- Error Responses nicht standardisiert — mal Detail, mal nacktes 500

---

## 2. Architektur-Entscheidungen

| Entscheidung | Wahl | Begruendung |
|---|---|---|
| Vault | Pflicht, kein Start ohne | Secrets gehoeren nicht in ENV. Governance. |
| Vault Init | Eigener Docker Service (`vault-init`) | Separation of Concerns, auditierbar, idempotent |
| Unseal | Hybrid: Auto-Unseal (Default), Manual/KMS (Enterprise) | KMU braucht Zero-Touch, Enterprise will Kontrolle. User entscheidet. |
| System-Secrets | Vault generiert automatisch | Kein CHANGE_ME in .env, kein menschlicher Fehler |
| LLM Keys | User gibt ein via Setup Wizard oder Settings | In Vault gespeichert, 60s TTL-Cache im Proxy |
| E2E Tests | Playwright + API-Tests, 30+ Szenarien | Happy Path + Error Cases + Edge Cases + Security |
| Logging | JSON Structured mit Request-ID | SIEM-kompatibel, end-to-end traceable |
| Errors | Standardisiertes Format | `{detail, code, request_id}` — nie nacktes 500 |

---

## 3. Vault-Init Service

### Docker Service

```yaml
vault-init:
  image: hashicorp/vault:1.17
  depends_on:
    vault:
      condition: service_healthy
  volumes:
    - nomos-vault:/vault/file
    - nomos-vault-init:/vault/init
    - ./vault/policies:/vault/policies:ro
    - ./vault/init.sh:/vault/init.sh:ro
  environment:
    - VAULT_ADDR=http://vault:8200
    - NOMOS_DB_PASSWORD=${NOMOS_DB_PASSWORD:?}
  entrypoint: ["/bin/sh", "/vault/init.sh"]
  restart: "no"
```

### Init-Script Ablauf

**Erster Start (nicht initialisiert):**

1. Warte auf Vault healthy (`curl` Loop, max 60s)
2. `vault operator init -key-shares=1 -key-threshold=1 -format=json`
3. Unseal Key → `/vault/init/unseal-key` (chmod 600)
4. Root Token → `/vault/init/root-token` (chmod 600)
5. `vault operator unseal`
6. `vault secrets enable -path=nomos -version=2 kv`
7. `vault policy write nomos-api /vault/policies/nomos-api.hcl`
8. `vault auth enable approle`
9. `vault write auth/approle/role/nomos-api token_policies=nomos-api token_ttl=1h`
10. Role ID + Secret ID → `/vault/init/approle-creds.env`
11. Generiere System-Secrets (openssl rand):
    - `jwt_secret` (64 Bytes, base64)
    - `plugin_api_key` (32 Bytes, hex, prefix `npk-`)
    - `gateway_token` (32 Bytes, hex, prefix `gw-`)
12. `vault kv put nomos/secrets/system jwt_secret=... plugin_api_key=... gateway_token=...`
13. `vault kv put nomos/secrets/database password=${NOMOS_DB_PASSWORD}`
14. Touch `/vault/init/initialized`
15. Log: `"Vault initialized successfully. Unseal key stored in /vault/init/unseal-key"`
16. Exit 0

**Restart (bereits initialisiert):**

1. Warte auf Vault healthy
2. Lese Unseal Key aus `/vault/init/unseal-key`
3. `vault operator unseal`
4. Verifiziere AppRole Credentials in `/vault/init/approle-creds.env`
5. Log: `"Vault unsealed (auto-unseal via init volume)"`
6. Exit 0

### Vault Policy (`vault/policies/nomos-api.hcl`)

```hcl
# NomOS API kann Secrets lesen und schreiben
path "nomos/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "nomos/metadata/*" {
  capabilities = ["read", "list"]
}

# Deny access to system secrets creation (nur init darf das)
# API kann lesen aber nicht die system-generierten Secrets ueberschreiben
```

### API Aenderungen

**config.py:**
```python
class Settings(BaseSettings):
    # Nur noch DB Password als ENV (fuer PostgreSQL Container)
    db_password: str

    # Vault Connection (aus Shared Volume gelesen)
    vault_addr: str = "http://vault:8200"
    vault_role_id: str = ""      # Aus /vault/init/approle-creds.env
    vault_secret_id: str = ""    # Aus /vault/init/approle-creds.env

    # Alles andere kommt aus Vault:
    # jwt_secret, plugin_api_key, gateway_token, llm_keys
    # → VaultSettingsSource mit 60s TTL-Cache
```

**VaultClient TTL-Cache:**
```python
class VaultClient:
    def __init__(self, ...):
        self._cache: dict[str, tuple[str, float]] = {}  # {path: (value, timestamp)}
        self._ttl = 60.0  # Sekunden

    def get_secret(self, path: str) -> str | None:
        # Cache Hit + nicht abgelaufen?
        if path in self._cache:
            value, ts = self._cache[path]
            if time.time() - ts < self._ttl:
                return value

        # Vault lesen + Cache aktualisieren
        value = self._read_from_vault(path)
        if value is not None:
            self._cache[path] = (value, time.time())
        return value
```

### .env wird minimal

```env
# NomOS — Minimal Configuration
# Nur 1 Pflichtfeld. Alles andere generiert Vault automatisch.

# PostgreSQL Passwort (wird beim ersten Start in Vault kopiert)
NOMOS_DB_PASSWORD=mein_sicheres_passwort

# LLM Provider (optional hier, kann auch spaeter via Console)
NVIDIA_API_KEY=nvapi-...

# Runtime
NOMOS_DEV_MODE=false
NOMOS_DOMAIN=localhost
```

---

## 4. First-Time Setup Wizard

### Trigger

Neuer API Endpoint: `GET /api/system/status`

```json
// Nicht initialisiert:
{
  "initialized": false,
  "vault_status": "healthy",
  "admin_exists": false,
  "setup_required": true
}

// Fertig:
{
  "initialized": true,
  "vault_status": "healthy",
  "admin_exists": true,
  "setup_required": false
}
```

Console prueft beim App-Load: `setup_required === true` → Redirect zu `/setup`

### `/setup` ist NUR erreichbar wenn `setup_required === true`

Danach gibt die Route 403 zurueck. Kein Zuruecknavigieren moeglich.

### Wizard Schritte

**Schritt 1: Vault-Sicherheitsschluessel**

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  🔐  Ihr Vault-Sicherheitsschlüssel                 │
│                                                      │
│  Dieser Schlüssel schützt ALLE Daten in NomOS.      │
│  Ohne ihn ist nach einem Datenverlust kein           │
│  Zugriff mehr möglich.                               │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  a3f8c2e1-9d4b-4f7a-b5c6-8e2d1f0a3b7c    │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  [📋 Kopieren]  [📄 Als PDF herunterladen]           │
│                                                      │
│  ⚠  Speichern Sie diesen Schlüssel an einem          │
│     sicheren Ort (Passwort-Manager, Tresor).         │
│     Er wird nach diesem Schritt NICHT MEHR            │
│     angezeigt.                                       │
│                                                      │
│  ☐ Ich habe den Schlüssel sicher gespeichert         │
│                                                      │
│                                          [Weiter →]  │
└─────────────────────────────────────────────────────┘
```

API: `GET /api/system/unseal-key` (einmalig abrufbar, danach 410 Gone)

**Schritt 2a: Administrator-Konto**

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  👤  Administrator-Konto erstellen                   │
│                                                      │
│  E-Mail:    [____________________]                   │
│  Passwort:  [____________________]  ████████░░ Stark │
│  Bestätigen:[____________________]                   │
│                                                      │
│  Mindestens 12 Zeichen, Gross-/Kleinbuchstaben,     │
│  Zahl und Sonderzeichen.                             │
│                                                      │
│  Ihr Wiederherstellungsschlüssel:                    │
│  ┌────────────────────────────────────────────┐      │
│  │  autumn aspect across artwork able art     │      │
│  │  autumn arrow among approve attend agent   │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  Dieser Schlüssel stellt Ihr Admin-Konto wieder     │
│  her wenn Sie Passwort UND 2FA verlieren.            │
│                                                      │
│  [📋 Kopieren]                                       │
│                                                      │
│  ☐ Ich habe den Wiederherstellungsschlüssel          │
│    sicher gespeichert                                │
│                                                      │
│                                          [Weiter →]  │
└─────────────────────────────────────────────────────┘
```

API: `POST /api/users/bootstrap` (wie bisher, aber mit Passwort-Validierung: min 12 Zeichen, Komplexitaet)

**Schritt 2b: Zwei-Faktor-Authentifizierung (optional)**

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  🔑  Zwei-Faktor-Authentifizierung                   │
│                                                      │
│  Empfohlen für maximale Sicherheit.                  │
│                                                      │
│  ┌──────────┐                                        │
│  │ QR Code  │  1. Öffnen Sie Ihre Authenticator-App │
│  │          │  2. Scannen Sie den QR-Code            │
│  │          │  3. Geben Sie den 6-stelligen Code ein │
│  └──────────┘                                        │
│                                                      │
│  Code: [______]                                      │
│                                                      │
│  [Jetzt aktivieren]  [Später in Einstellungen]       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

API: `POST /api/auth/2fa/setup` + `POST /api/auth/2fa/verify`

**Schritt 3: KI-Provider konfigurieren**

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  🤖  KI-Provider konfigurieren                       │
│                                                      │
│  Wählen Sie einen Anbieter für Ihre KI-Agenten:     │
│                                                      │
│  ○ NVIDIA (empfohlen, kostenloser Einstieg)          │
│    API Key: [nvapi-___________________]              │
│    https://build.nvidia.com                          │
│                                                      │
│  ○ OpenAI                                            │
│    API Key: [sk-_____________________]               │
│    https://platform.openai.com                       │
│                                                      │
│  ○ Anthropic                                         │
│    API Key: [sk-ant-_________________]               │
│    https://console.anthropic.com                     │
│                                                      │
│  [🔍 Key testen]  Ergebnis: ✓ Verbindung OK         │
│                                                      │
│  [Weiter →]            [Später konfigurieren →]      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

API: `PATCH /api/settings` (schreibt Key in Vault)
Test: `POST /api/proxy/status` (prueft ob Provider erreichbar)

**Schritt 4: Zusammenfassung**

```
┌─────────────────────────────────────────────────────┐
│                                                      │
│  ✓  NomOS ist bereit!                                │
│                                                      │
│  Vault-Verschlüsselung     ✓ Aktiv                  │
│  Administrator              ✓ admin@example.com      │
│  Zwei-Faktor-Auth           ✓ Aktiviert / ○ Später  │
│  KI-Provider                ✓ NVIDIA / ○ Später     │
│                                                      │
│  Auto-Entsperrung ist aktiv. Vault wird bei          │
│  jedem Neustart automatisch entsperrt.               │
│  [Mehr erfahren]                                     │
│                                                      │
│              [🚀 NomOS starten]                      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Zwei Keys — klare Kommunikation

| Key | Schuetzt | Wann noetig | Konsequenz ohne |
|---|---|---|---|
| **Vault-Sicherheitsschluessel** | Alle Daten (Secrets, Configs, Memory) | Server-Migration, Datenbank-Recovery | Alle verschluesselten Daten verloren |
| **Wiederherstellungsschluessel** | Admin-Konto | Passwort + 2FA verloren | Konto gesperrt, Daten sicher, neuen Admin via CLI |

---

## 5. Structured Logging

### Format

Jeder Log-Eintrag ist JSON:

```json
{
  "timestamp": "2026-04-05T18:30:00.123Z",
  "level": "INFO",
  "logger": "nomos-api",
  "message": "POST /api/agents 201",
  "request_id": "req-abc123",
  "method": "POST",
  "path": "/api/agents",
  "status": 201,
  "duration_ms": 45,
  "user_id": "admin-uuid",
  "agent_id": "selina",
  "vault_status": "healthy"
}
```

### Request Correlation

```
Frontend                    API                         Vault
  │                          │                           │
  │ X-Request-ID: req-abc123 │                           │
  ├─────────────────────────>│                           │
  │                          │ request_id: req-abc123    │
  │                          ├──────────────────────────>│
  │                          │                           │
  │ 200 OK                   │                           │
  │<─────────────────────────│                           │
```

Frontend generiert `X-Request-ID` bei jedem API Call. API loggt alle Aktionen mit dieser ID. `docker logs nomos-nomos-api-1 | jq 'select(.request_id == "req-abc123")'` zeigt den kompletten Request-Lifecycle.

### Error Response Standard

Jeder Error folgt:

```json
{
  "detail": "Agent 'selina' nicht gefunden.",
  "code": "AGENT_NOT_FOUND",
  "request_id": "req-abc123"
}
```

Nie ein nacktes `{"detail": "Internal Server Error"}` ohne Code und Request-ID.

### Health Endpoint erweitert

```json
GET /health
{
  "status": "healthy",
  "service": "NomOS Fleet API",
  "version": "0.1.0",
  "components": {
    "vault": "healthy",
    "postgres": "healthy",
    "valkey": "healthy",
    "gateway": "online",
    "worker": "healthy"
  },
  "uptime_seconds": 3600
}
```

Nicht nur "healthy/unhealthy" — sondern WAS genau kaputt ist.

---

## 6. E2E Tests — Vollstaendig

### Playwright Browser Tests (20 Szenarien)

**Happy Path:**

| # | Test | Prueft |
|---|---|---|
| 1 | Login Happy Path | Email + Passwort → Dashboard |
| 2 | Hire Wizard komplett | 4 Schritte → Agent compliant |
| 3 | Chat Happy Path | Nachricht → LLM antwortet |
| 4 | Settings aendern | Retention Days → Speichern → Reload → Wert bleibt |
| 5 | Agent pausieren/resumieren | Button → Status wechselt |
| 6 | Compliance Tab | Alle Dokumente gruen |
| 7 | Audit Trail | Eintraege sichtbar mit Hash |
| 8 | Multi-User RBAC | User sieht nur eigene Agents |
| 9 | Admin Audit | Admin pausiert fremden Agent → Audit-Eintrag |
| 10 | Diagnostics Page | Alle Services gruen |

**Error Cases:**

| # | Test | Prueft |
|---|---|---|
| 11 | Login falsches Passwort | 401 → Fehlermeldung, kein Crash |
| 12 | Session abgelaufen | Redirect zu Login, nicht weisse Seite |
| 13 | Doppelt Hire gleicher Name | Klare Fehlermeldung, kein 500 |
| 14 | Chat waehrend Agent Pause | "Agent ist pausiert" Message |
| 15 | Leere Nachricht senden | Button disabled, kein API Call |
| 16 | Chat ohne Provider | Gelbes Banner mit Settings-Link |

**Infrastructure Failure:**

| # | Test | Prueft |
|---|---|---|
| 17 | API offline waehrend Chat | Error-Message im Chat |
| 18 | Gateway offline | "Chat-Dienst nicht erreichbar" |
| 19 | Vault offline → Settings | Fehlermeldung, keine Daten verloren |
| 20 | Concurrent Chat | 2 Tabs gleichzeitig, kein Race Condition |

### API Integration Tests (16 Szenarien)

**Functional:**

| # | Test | Endpoint |
|---|---|---|
| 1 | Health + alle Components | GET /health → postgres, vault, valkey, gateway |
| 2 | System Status | GET /api/system/status → initialized, admin_exists |
| 3 | Bootstrap + Login + Token | POST /users/bootstrap, /auth/login |
| 4 | Agent CRUD + Compliance | POST /agents → compliance: passed |
| 5 | Budget Check unknown | POST /budget/check → unknown_agent |
| 6 | Settings PATCH → Vault → GET | Wert persistiert |
| 7 | DSGVO Forget | POST /dsgvo/forget → deleted, audit erhalten |
| 8 | Audit Hash Chain Verify | GET /audit/verify/{id} → valid chain |

**Error + Edge Cases:**

| # | Test | Endpoint |
|---|---|---|
| 9 | Ungueltige JSON | POST /agents → 422 |
| 10 | Fehlende Pflichtfelder | POST /agents ohne name → 422 mit Feld-Error |
| 11 | Agent nicht gefunden | GET /fleet/nonexistent → 404 |
| 12 | Abgelaufener Token | Request mit expired JWT → 401 |
| 13 | Rate Limit | 20x /auth/login → 429 |
| 14 | RBAC User → fremder Agent | POST /agents/{id}/pause → 403 |
| 15 | DB offline | 503 mit klarer Message |
| 16 | Vault sealed → Settings | Fallback oder klarer Error |

**Security:**

| # | Test | Prueft |
|---|---|---|
| 17 | XSS in Agent-Name | `<script>` wird escaped |
| 18 | SQL Injection in Agent-Name | Pydantic validiert |
| 19 | HTTPS Redirect | HTTP → 301 → HTTPS |
| 20 | Security Headers | HSTS, CSP, X-Frame, X-Content |

### Debugging-Infrastruktur

| Feature | Was es tut |
|---|---|
| **JSON Structured Logs** | `docker logs nomos-nomos-api-1 \| jq '.level == "ERROR"'` |
| **Request Correlation ID** | `X-Request-ID` Header end-to-end |
| **Error Response Standard** | `{detail, code, request_id}` immer |
| **Health Components** | `/health` zeigt Status jeder Komponente |
| **Diagnostics Page** | Console zeigt Service-Status, letzte Errors |

### CI Integration

```yaml
# .github/workflows/ci.yml
e2e-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: docker compose up -d
    - run: sleep 60  # Warten auf healthy
    - run: docker compose ps  # Verify 8/8 healthy
    - run: npx playwright test  # 20 Browser Tests
    - run: python -m pytest tests/integration/  # 20 API Tests
    - run: docker compose down -v
```

---

## 7. Reihenfolge

```
Phase A: Vault-Init Service (Fundament)
  1. vault-init Docker Service + init.sh
  2. VaultClient TTL-Cache
  3. config.py: Secrets aus Vault statt ENV
  4. .env minimal (nur DB_PASSWORD)
  5. Tests: Vault Init, Secret Read, TTL-Cache

Phase B: Setup Wizard (User-Facing)
  1. GET /api/system/status Endpoint
  2. GET /api/system/unseal-key (einmalig)
  3. Console: /setup Route mit 4 Wizard-Schritten
  4. Passwort-Validierung (min 12, Komplexitaet)
  5. 2FA optional im Wizard
  6. Tests: Setup Flow E2E

Phase C: Structured Logging + Error Standard
  1. JSON Logger konfigurieren
  2. X-Request-ID Middleware
  3. Error Response Schema
  4. Health Endpoint erweitern
  5. Diagnostics Page updaten

Phase D: E2E Test Suite
  1. Playwright Setup gegen Docker
  2. 20 Browser Tests
  3. 20 API Integration Tests
  4. CI Pipeline Integration

Phase E: Integration Test
  → docker compose up + Browser + kompletter Flow
  → Rule 06: Pflicht vor "fertig"
```

**Geschaetzter Gesamtaufwand: ~20 Stunden**

---

## 8. Abnahme-Kriterien

```
1. docker compose up -d (NUR mit NOMOS_DB_PASSWORD in .env)
   → Vault-Init laeuft automatisch
   → Alle Secrets in Vault generiert
   → 9/9 Services healthy (inkl. vault-init exit 0)

2. Browser → /setup Wizard
   → Unseal Key angezeigt + gesichert
   → Admin erstellt (min 12 Zeichen)
   → Optional 2FA aktiviert
   → LLM Key eingegeben + getestet
   → Redirect zu Dashboard

3. Hire → Chat → Antwort
   → Agent sofort compliant
   → LLM antwortet
   → Error Cases zeigen klare Messages

4. docker compose restart
   → Vault wird automatisch unsealed
   → Alle Services starten
   → Kein manueller Eingriff

5. 40 E2E Tests gruen
   → 20 Playwright + 20 API
   → Happy Path + Error Cases + Security

6. docker logs ... | jq
   → JSON Format, Request-IDs, Error Codes
```

---

## 9. Was NICHT in diesem Scope ist

- Multi-Turn Chat (Sub-Projekt A, naechste Phase)
- Agent Persona / System Prompt (Sub-Projekt A)
- Honcho Memory Integration (Sub-Projekt A)
- NemoClaw Container Isolation
- Pixel Office UI
- WebSocket Live Updates
- KMS Auto-Unseal Implementierung (dokumentiert als Upgrade-Pfad)
