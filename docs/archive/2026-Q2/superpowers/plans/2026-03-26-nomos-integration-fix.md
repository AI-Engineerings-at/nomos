# NomOS v2 Integration Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Docker Stack laeuft komplett, Auth auf allen Routes, Plugin-Endpoints stimmen, Console Login funktioniert — EIN End-to-End Flow (Login → Hire → Chat → Pause) im Browser verifiziert.

**Architecture:** Fixes am bestehenden Code, keine neuen Features. Gateway Config aus verifizierter Doku (`docs/references/openclaw-nemoclaw-reference.md`). Plugin Entry Point auf `definePluginEntry()` umstellen. API Endpoint-Pfade an Plugin-Erwartungen angleichen. Console Login-Response an API angleichen. Auth Middleware global anwenden.

**Tech Stack:** Python 3.12 (FastAPI), TypeScript strict (Next.js 15, OpenClaw Plugin SDK), PostgreSQL, Valkey, Docker Compose

**Referenzen:**
- OpenClaw/NemoClaw Referenz: `docs/references/openclaw-nemoclaw-reference.md`
- Postmortem: `docs/reports/2026-03-25-session-postmortem.md`
- Design Spec: `docs/superpowers/specs/2026-03-24-nomos-v2-design.md`

---

## Bekannte Mismatches (aus Codebase-Analyse)

| # | Plugin ruft auf | API hat | Fix |
|---|----------------|---------|-----|
| 1 | `POST /api/compliance/gate` `{agent_id}` | `POST /api/agents/{agent_id}/gate` | API: Alias-Route hinzufuegen |
| 2 | `POST /api/budget/check` `{agent_id, estimated_cost}` | Existiert NICHT | API: Endpoint erstellen |
| 3 | `POST /api/audit/entry` | Existiert ✓ | OK |
| 4 | `POST /api/pii/filter` | Existiert ✓ | OK |
| 5 | `POST /api/incidents` `{agent_id, description, severity}` | Existiert aber erwartet `{log_entry, agent_id, context}` | Plugin: Felder anpassen |
| 6 | `POST /api/agents/{id}/heartbeat` | Existiert ✓ | OK |
| 7 | `POST /api/agents/{id}/pause` | Existiert ✓ | OK |
| 8 | `GET /api/health` | `GET /health` (kein /api Prefix) | Plugin: Pfad anpassen |

| # | Console erwartet | API liefert | Fix |
|---|-----------------|-------------|-----|
| 1 | `LoginResponse { requires_2fa, user: {id,email,name,role} }` | `LoginResponse { message, role, email }` | API: Response anpassen |
| 2 | `GET /api/auth/me` → `{id, email, name, role}` | Existiert ✓ aber Response pruefen | Verifizieren |

| # | docker-compose Problem | Fix |
|---|----------------------|-----|
| 1 | Gateway Health Check: `/health` statt `/healthz` | Aendern auf `/healthz` |
| 2 | Gateway Plugin-Mount: `/plugins/nomos:ro` statt `/home/node/.openclaw/extensions/nomos:ro` | Pfad anpassen |
| 3 | Gateway Config fehlt: Keine `openclaw.json` gemountet | Config-Datei erstellen + mounten |
| 4 | JWT Secret hardcoded Default | Env-Var Pflicht machen |
| 5 | CORS nur localhost:3040,3045 | Passt fuer Docker, OK |

---

## Task 1: Gateway Config erstellen + docker-compose fixen

**Files:**
- Create: `config/openclaw.json`
- Modify: `docker-compose.yml:8-29`

- [ ] **Step 1: Gateway Config Datei erstellen**

Basierend auf verifizierter Kimi-Referenz (`docs/references/openclaw-nemoclaw-reference.md` Section 2):

```json
{
  "tools": {
    "profile": "coding",
    "fs": { "workspaceOnly": true }
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true
  },
  "session": {
    "dmScope": "per-channel-peer"
  },
  "discovery": {
    "mdns": { "mode": "off" }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "enabled": false
    },
    "auth": {
      "mode": "token",
      "token": "nomos-dev-token"
    }
  }
}
```

Alle Keys aus der verifizierten Kimi-Referenz uebernommen (R1: nicht selektiv kuerzen).

Speichern als `config/openclaw.json`.

- [ ] **Step 2: docker-compose.yml Gateway-Service fixen**

```yaml
  openclaw-gateway:
    image: ghcr.io/openclaw/openclaw:latest
    ports:
      - "${NOMOS_GATEWAY_PORT:-3050}:18789"
    volumes:
      - ./config/openclaw.json:/home/node/.openclaw/openclaw.json:ro
      - ./nomos-plugin/dist:/home/node/.openclaw/extensions/nomos:ro
      - nomos-agents:/home/node/.openclaw/workspace
    depends_on:
      valkey:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:18789/healthz"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
```

Aenderungen:
1. Config mount: `/home/node/.openclaw/openclaw.json:ro`
2. Plugin mount: `/home/node/.openclaw/extensions/nomos:ro` (statt `/plugins/nomos`)
3. Workspace mount: `/home/node/.openclaw/workspace`
4. Health check: `/healthz` (statt `/health`)
5. Entfernt: `OPENCLAW_GATEWAY_PORT`, `OPENCLAW_GATEWAY_BIND`, `OPENCLAW_PLUGINS_DIR`, `OPENCLAW_AGENTS_DIR` ENV vars (Config kommt aus Datei)

- [ ] **Step 3: Verzeichnis erstellen**

```bash
mkdir -p config
```

- [ ] **Step 4: Commit**

```bash
git add config/openclaw.json docker-compose.yml
git commit -m "fix(gateway): correct config mount, healthz endpoint, plugin path per OpenClaw docs"
```

**GATE:** `docker compose config` zeigt keine Syntax-Fehler.

---

## Task 2: Plugin Entry Point auf definePluginEntry umstellen

**Files:**
- Modify: `nomos-plugin/src/index.ts:1-75`
- Modify: `nomos-plugin/package.json` (dependency pruefen)

- [ ] **Step 1: Pruefen ob openclaw SDK als Dependency verfuegbar ist**

```bash
cd nomos-plugin && cat package.json | grep -i openclaw
```

Wenn `openclaw` NICHT in dependencies: Das Plugin laeuft im Gateway-Prozess, der SDK ist zur Laufzeit verfuegbar. Wir koennen trotzdem den richtigen Entry Point verwenden — der Import wird zur Laufzeit aufgeloest.

- [ ] **Step 2: index.ts umschreiben**

Von:
```typescript
export default function register(api: OpenClawPluginApi): void {
```

Zu:
```typescript
// Option A: Wenn openclaw SDK verfuegbar
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export default definePluginEntry({
  id: "nomos",
  name: "NomOS",
  description: "EU AI Act + DSGVO compliance enforcement for OpenClaw agents",
  register(api) {
    // ... bestehender Hook-Code bleibt gleich
  },
});
```

ODER wenn der SDK Import nicht funktioniert (Plugin wird zur Laufzeit in den Gateway injected):

```typescript
// Option B: Behalte export default function, aber pruefe ob Gateway es akzeptiert
export default function register(api: OpenClawPluginApi): void {
  // ... bestehender Code
}
```

**WICHTIG:** R1 — Erst im laufenden Gateway testen welches Format funktioniert. Nicht raten.

- [ ] **Step 3: Plugin Health-Check Pfad fixen**

In `nomos-plugin/src/hooks/gateway-start.ts` oder `api-client.ts`:
Wenn der Plugin `GET /api/health` aufruft, aendern zu `GET /health` (API hat keinen /api Prefix fuer Health).

```bash
grep -rn "api/health" nomos-plugin/src/
```

- [ ] **Step 4: Plugin bauen**

```bash
cd nomos-plugin && npm run build
```

Erwartung: `dist/index.js` wird erstellt ohne Fehler.

- [ ] **Step 5: Commit**

```bash
git add nomos-plugin/src/index.ts nomos-plugin/dist/
git commit -m "fix(plugin): update entry point format, fix health check path"
```

**GATE:** `npm run build` erfolgreich. `dist/index.js` existiert.

---

## Task 3: API Endpoint-Mismatches fixen

**Files:**
- Modify: `nomos-api/nomos_api/routers/compliance.py`
- Create: `nomos-api/nomos_api/routers/budget.py`
- Modify: `nomos-api/nomos_api/main.py`

- [ ] **Step 1: Compliance Gate Alias-Route hinzufuegen**

Plugin ruft `POST /api/compliance/gate` auf. API hat `POST /api/agents/{agent_id}/gate`.

In `nomos-api/nomos_api/routers/compliance.py` eine Alias-Route hinzufuegen:

```python
@router.post("/compliance/gate", response_model=ComplianceResponse)
async def compliance_gate_alias(
    request: dict,
    db: AsyncSession = Depends(get_db),
) -> ComplianceResponse:
    """Alias for plugin compatibility: POST /api/compliance/gate {agent_id}"""
    agent_id = request.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    return await run_compliance_gate(agent_id, db)
```

- [ ] **Step 2: Budget Check Endpoint erstellen**

Plugin ruft `POST /api/budget/check` auf. Dieser Endpoint existiert nicht.

In `nomos-api/nomos_api/routers/budget.py`:

```python
"""Budget check endpoint — called by NomOS Plugin before_tool_call hook."""

from fastapi import APIRouter
from pydantic import BaseModel

from nomos_api.services.budget import BudgetService

router = APIRouter(prefix="/api", tags=["budget"])

_budget_service = BudgetService()


class BudgetCheckRequest(BaseModel):
    agent_id: str
    estimated_cost: float = 0.0


@router.post("/budget/check")
async def check_budget(request: BudgetCheckRequest) -> dict:
    """Check if agent has budget for estimated cost.

    NOTE: BudgetService.check() requires 4 args: agent_id, current, limit, warn_at.
    Current cost is tracked in-memory. Limit defaults to 100 EUR, warn_at to 80%.
    This is an in-memory implementation (known S9 limitation — to be replaced with DB).
    """
    current = _budget_service._costs.get(request.agent_id, 0.0)
    # Add estimated cost to current for check
    projected = current + request.estimated_cost
    # Default limits — should come from agent manifest/DB in future
    limit = 100.0
    warn_at = 80
    result = _budget_service.check(request.agent_id, projected, limit, warn_at)
    return {
        "allowed": result.get("allowed", True),
        "remaining": max(0, limit - projected),
        "status": result.get("status", "normal"),
        "error": None if result.get("allowed") else "Budget exceeded",
    }
```

**Bekannte Limitation:** BudgetService ist in-memory (S9). Wird in zukuenftigem Task durch DB-backed Service ersetzt.

- [ ] **Step 3: Budget Router in main.py registrieren**

In `nomos-api/nomos_api/main.py`, nach den anderen Router-Imports:

```python
from nomos_api.routers import budget
# ...
app.include_router(budget.router)
```

- [ ] **Step 4: Plugin Incidents Felder fixen**

Plugin sendet `{ agent_id, description, severity }` aber API erwartet `{ log_entry, agent_id, context }`.

In `nomos-plugin/src/hooks/on-error.ts` (oder wo `reportIncident` aufgerufen wird):

```typescript
// Von:
await client.reportIncident({ agent_id, description: error.message, severity: "high" });

// Zu:
await client.reportIncident({
  log_entry: error.message,
  agent_id,
  context: { severity: "high", hook: hookName },
});
```

In `nomos-plugin/src/api-client.ts`, `reportIncident` Methode anpassen:

```typescript
async reportIncident(data: { log_entry: string; agent_id: string; context?: Record<string, unknown> }): Promise<boolean> {
  const res = await fetch(`${this.baseUrl}/api/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.ok;
}
```

- [ ] **Step 5: Health Check Pfad in Plugin fixen**

In `nomos-plugin/src/api-client.ts`, die Health-Check Methode:

```typescript
// Von:
async healthCheck(): Promise<boolean> {
  const res = await fetch(`${this.baseUrl}/api/health`);
  // Zu:
  const res = await fetch(`${this.baseUrl}/health`);
```

- [ ] **Step 6: Tests ausfuehren**

```bash
cd nomos-api && python -m pytest tests/ -x -q
cd nomos-plugin && npm test
```

Erwartung: Alle bestehenden Tests PASS.

- [ ] **Step 7: Commit**

```bash
git add nomos-api/nomos_api/routers/compliance.py nomos-api/nomos_api/routers/budget.py nomos-api/nomos_api/main.py nomos-plugin/src/
git commit -m "fix(api+plugin): endpoint alignment — compliance gate alias, budget check, incidents fields, health path"
```

**GATE:** `pytest` PASS. Neue Endpoints erreichbar (testen in Task 7).

---

## Task 4: API Login Response an Console angleichen

**Files:**
- Modify: `nomos-api/nomos_api/routers/auth.py`
- Modify: `nomos-api/nomos_api/schemas.py` (LoginResponse)

- [ ] **Step 1: Aktuellen LoginResponse lesen**

```bash
grep -A 5 "class LoginResponse" nomos-api/nomos_api/schemas.py
```

Aktuell: `{ message: str, role: str, email: str }`
Console erwartet: `{ requires_2fa: bool, user: { id, email, name, role } }`

- [ ] **Step 2: LoginResponse Schema anpassen**

In `nomos-api/nomos_api/schemas.py`:

```python
class LoginUserInfo(BaseModel):
    id: str
    email: str
    name: str
    role: str

class LoginResponse(BaseModel):
    requires_2fa: bool = False
    user: LoginUserInfo | None = None
    message: str | None = None
```

- [ ] **Step 3: Login Endpoint anpassen**

In `nomos-api/nomos_api/routers/auth.py`, die login() Funktion:
Nach erfolgreicher Authentifizierung:

```python
return LoginResponse(
    requires_2fa=user.totp_enabled,
    user=LoginUserInfo(
        id=str(user.id),
        email=user.email,
        name=user.email.split("@")[0],  # Fallback wenn kein name-Feld
        role=user.role,
    ) if not user.totp_enabled else None,
    message="Login successful",
)
```

- [ ] **Step 4: Tests anpassen und ausfuehren**

```bash
cd nomos-api && grep -rn "LoginResponse" tests/ | head -10
```

Bestehende Login-Tests an neues Format anpassen. Dann:

```bash
python -m pytest tests/ -x -q
```

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/schemas.py nomos-api/nomos_api/routers/auth.py nomos-api/tests/
git commit -m "fix(auth): align login response with console expectations (requires_2fa + user object)"
```

**GATE:** Login-Tests PASS. Response Format stimmt mit Console ueberein.

---

## Task 5: Auth Middleware global anwenden

**Files:**
- Modify: `nomos-api/nomos_api/main.py`
- Modify: `nomos-api/nomos_api/auth/middleware.py`

- [ ] **Step 1: Aktuelle Auth-Situation pruefen**

```bash
grep -rn "Depends.*current_user\|require_admin\|require_role" nomos-api/nomos_api/routers/ | head -20
```

Feststellen: Welche Routen haben KEINE Auth.

- [ ] **Step 2: Auth Middleware als FastAPI Dependency global anwenden**

In `nomos-api/nomos_api/main.py`:

```python
import jwt
from starlette.responses import JSONResponse

# Public routes that don't need auth
PUBLIC_PATHS = {
    "/health",
    "/api/auth/login",
    "/api/auth/recovery",
    "/api/users/bootstrap",
    "/docs",
    "/openapi.json",
}

@app.middleware("http")
async def global_auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
        return await call_next(request)
    # Check JWT cookie
    token = request.cookies.get("nomos_token")
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        request.state.user = payload
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    return await call_next(request)
```

- [ ] **Step 3: Plugin-Aufrufe beruecksichtigen**

Das Plugin ruft API Endpoints OHNE Cookie auf (Service-to-Service). Loesung: Plugin sendet einen API-Key Header.

In der Middleware:
```python
# Service-to-service auth (Plugin → API)
api_key = request.headers.get("X-NomOS-API-Key")
if api_key and api_key == settings.plugin_api_key:
    request.state.user = {"role": "service", "email": "plugin@nomos.local"}
    return await call_next(request)
```

Neues ENV: `NOMOS_PLUGIN_API_KEY` in docker-compose fuer API + Gateway Service.

In `nomos-plugin/src/api-client.ts`, Header zu jedem fetch hinzufuegen:
```typescript
headers: {
  "Content-Type": "application/json",
  "X-NomOS-API-Key": config.pluginApiKey || process.env.NOMOS_PLUGIN_API_KEY || "",
}
```

In `docker-compose.yml` Gateway-Service Environment hinzufuegen:
```yaml
    environment:
      - NOMOS_PLUGIN_API_KEY=${NOMOS_PLUGIN_API_KEY:-nomos-plugin-dev}
```

- [ ] **Step 4: Tests anpassen**

Bestehende Tests die OHNE Auth Endpoints aufrufen brauchen einen Test-User oder die Test-Fixtures muessen Auth-Cookies setzen.

```bash
cd nomos-api && python -m pytest tests/ -x -q 2>&1 | head -20
```

Fehler fixen bis alle Tests PASS.

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/main.py nomos-api/nomos_api/auth/ nomos-api/tests/
git commit -m "fix(auth): apply global auth middleware, add service-to-service API key for plugin"
```

**GATE:** Alle Tests PASS. Unauthentifizierte Requests zu geschuetzten Endpoints → 401.

---

## Task 6: JWT Secret + Plugin API Key in docker-compose

**Files:**
- Modify: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: .env.example erstellen**

```env
# NomOS Environment Configuration
# Copy to .env and change values for production

NOMOS_JWT_SECRET=change-me-min-32-chars-random
NOMOS_PLUGIN_API_KEY=change-me-plugin-key
NOMOS_DB_PASSWORD=nomos
NOMOS_GATEWAY_PORT=3050
NOMOS_API_PORT=8060
NOMOS_CONSOLE_PORT=3040
```

- [ ] **Step 2: docker-compose.yml anpassen**

API Service:
```yaml
    environment:
      - NOMOS_JWT_SECRET=${NOMOS_JWT_SECRET:?Set NOMOS_JWT_SECRET in .env}
      - NOMOS_PLUGIN_API_KEY=${NOMOS_PLUGIN_API_KEY:-nomos-plugin-dev}
```

- [ ] **Step 3: .env fuer Dev erstellen**

```bash
cp .env.example .env
# Dev-Defaults sind OK fuer lokale Entwicklung
sed -i 's/change-me-min-32-chars-random/dev-secret-not-for-production-use-32ch/' .env
sed -i 's/change-me-plugin-key/dev-plugin-key/' .env
```

- [ ] **Step 4: .gitignore pruefen**

```bash
grep "^\.env$" .gitignore || echo ".env" >> .gitignore
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .env.example .gitignore
git commit -m "fix(security): JWT secret from env, plugin API key, .env.example template"
```

**GATE:** `docker compose config` zeigt keine Fehler. `.env` ist gitignored.

---

## Task 7: Docker Stack starten + verifizieren

**Files:** Keine Code-Aenderungen. Nur Verifizierung.

- [ ] **Step 1: Plugin bauen**

```bash
cd nomos-plugin && npm run build
ls dist/index.js
```

- [ ] **Step 2: Stack starten**

```bash
cd /c/Users/Legion/Documents/nomos
docker compose up -d --build
```

- [ ] **Step 3: Alle Services healthy?**

```bash
docker compose ps
```

Erwartung: Alle Services `healthy` oder `running`. Kein Service `unhealthy` oder `exited`.

- [ ] **Step 4: Gateway Health Check**

```bash
curl -sf http://localhost:3050/healthz
```

Erwartung: HTTP 200.

- [ ] **Step 5: API Health Check**

```bash
curl -sf http://localhost:8060/health
```

Erwartung: `{"status": "ok", "service": "NomOS API v2"}`

- [ ] **Step 6: Gateway Logs pruefen — Plugin geladen?**

```bash
docker compose logs openclaw-gateway 2>&1 | grep -i "nomos\|plugin\|extension"
```

Erwartung: NomOS Plugin Banner oder "loaded" Meldung.

- [ ] **Step 7: Wenn Gateway Plugin NICHT laedt**

R1: Nicht raten. Logs lesen. OpenClaw Doku pruefen (`docs/references/openclaw-nemoclaw-reference.md`).

Moegliche Ursachen:
- Plugin-Pfad falsch (pruefen ob `/home/node/.openclaw/extensions/nomos/` existiert im Container)
- Plugin Entry Point Format falsch (definePluginEntry vs export default)
- Plugin Build-Fehler

```bash
docker compose exec openclaw-gateway ls /home/node/.openclaw/extensions/nomos/
docker compose exec openclaw-gateway cat /home/node/.openclaw/extensions/nomos/openclaw.plugin.json
```

- [ ] **Step 8: Blockiert? → Joe informieren**

Wenn Gateway Plugin nach 3 Versuchen nicht laedt: STOP. Joe informieren mit:
1. Was versucht wurde
2. Was die Logs sagen
3. Welche Doku gelesen wurde

**GATE:** Alle 5 Services healthy. Gateway zeigt Plugin als geladen.

---

## Task 8: Bootstrap Admin + Console Login testen

**Files:** Keine Code-Aenderungen. Verifizierung im Browser.

- [ ] **Step 1: Admin-User erstellen**

```bash
curl -X POST http://localhost:8060/api/users/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nomos.local","password":"Admin123!","role":"admin"}'
```

Erwartung: 201 mit User-Daten.

- [ ] **Step 2: Login testen (API direkt)**

```bash
curl -v -X POST http://localhost:8060/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nomos.local","password":"Admin123!"}'
```

Erwartung:
- HTTP 200
- `set-cookie: nomos_token=...`
- Body: `{"requires_2fa": false, "user": {"id": "...", "email": "admin@nomos.local", "name": "admin", "role": "admin"}}`

- [ ] **Step 3: Console im Browser oeffnen**

```
http://localhost:3040
```

Erwartung: Login-Seite wird angezeigt.

- [ ] **Step 4: Login im Browser**

Email: `admin@nomos.local`, Password: `Admin123!`

Erwartung:
- Login erfolgreich
- Redirect zu `/admin` (weil role=admin)
- Dashboard wird angezeigt (darf leer sein, aber kein Crash)

- [ ] **Step 5: F12 Console pruefen**

Browser Developer Tools oeffnen (F12). Console-Tab pruefen.

Erwartung: Keine roten Fehler die den Login oder die Navigation betreffen.

- [ ] **Step 6: Blockiert? → Joe informieren**

Wenn Login nicht funktioniert: Exakt dokumentieren WAS passiert (HTTP Status, Response Body, F12 Fehler) und Joe zeigen.

**GATE:** Login im Browser funktioniert. User wird auf Dashboard weitergeleitet.

---

## Task 9: Hire Agent E2E testen

**Files:** Keine Code-Aenderungen. Verifizierung.

- [ ] **Step 1: Agent erstellen (API)**

```bash
curl -X POST http://localhost:8060/api/agents \
  -H "Content-Type: application/json" \
  -H "Cookie: nomos_token=<TOKEN_AUS_STEP_8>" \
  -d '{"name":"Mani","role":"Social Media Manager","company":"Test GmbH","email":"mani@test.local","risk_class":"limited"}'
```

Erwartung: 201 mit AgentResponse.

- [ ] **Step 2: Fleet pruefen**

```bash
curl http://localhost:8060/api/fleet
```

Erwartung: Mani ist in der Agent-Liste mit Status "deploying" oder "running".

- [ ] **Step 3: Agent pausieren**

```bash
curl -X POST http://localhost:8060/api/agents/<AGENT_ID>/pause \
  -H "Cookie: nomos_token=<TOKEN>"
```

Erwartung: 200, Status = "paused".

- [ ] **Step 4: Agent resumieren**

```bash
curl -X POST http://localhost:8060/api/agents/<AGENT_ID>/resume \
  -H "Cookie: nomos_token=<TOKEN>"
```

Erwartung: 200, Status = "running".

- [ ] **Step 5: Im Browser pruefen**

Console oeffnen → Team/Fleet Seite → Mani sollte sichtbar sein.

**GATE:** Agent Lifecycle funktioniert: Create → Pause → Resume. Sichtbar in Console.

---

## Task 10: Cleanup + Dokumentation

**Files:**
- Modify: `nomos/.claude/CLAUDE.md` (Quick Commands hinzufuegen)

- [ ] **Step 1: Verwaiste Worktrees aufraeumen**

```bash
git worktree list
# Fuer jede verwaiste Worktree:
git worktree remove .claude/worktrees/<name> --force
```

- [ ] **Step 2: Quick Commands zu CLAUDE.md hinzufuegen**

In `nomos/.claude/CLAUDE.md` nach Tech Stack:

```markdown
## Quick Commands
```bash
docker compose up -d --build          # Start all services
docker compose ps                     # Check health
docker compose logs -f openclaw-gateway  # Gateway logs
cd nomos-api && python -m pytest tests/ -x -q  # API tests
cd nomos-cli && python -m pytest tests/ -x -q  # CLI tests
cd nomos-plugin && npm run build && npm test    # Plugin build + test
ruff check nomos-api nomos-cli        # Lint Python
```
```

- [ ] **Step 3: open-notebook aktualisieren**

```bash
curl -s -X POST http://10.40.10.82:5055/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"NomOS Integration Fix abgeschlossen (26.03.2026)","content":"..."}'
```

- [ ] **Step 4: ERPNext Task updaten**

TASK-2026-00409 auf "Completed" setzen.

- [ ] **Step 5: Final Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: add quick commands to CLAUDE.md, cleanup worktrees"
```

**GATE:** Stack laeuft. Login funktioniert. Agent Lifecycle funktioniert. Docs aktuell.

---

## Reihenfolge + Abhaengigkeiten

```
Task 1 (Gateway Config)        ← MUSS ZUERST (Fundament)
  ↓
Task 2 (Plugin Entry Point)    ← Braucht korrekten Gateway
  ↓
Task 3 (API Endpoints)         ← Plugin muss wissen was es aufruft
  ↓
Task 4 (Login Response)        ← Console braucht korrekte API Response
  ↓
Task 5 (Auth Middleware)       ← Alle Routes schuetzen
  ↓
Task 6 (JWT + Plugin Key)      ← Auth braucht Secrets
  ↓
Task 7 (Stack starten)         ← ALLES zusammen testen
  ↓
Task 8 (Login E2E)             ← Browser-Test
  ↓
Task 9 (Hire E2E)              ← Vollstaendiger Flow
  ↓
Task 10 (Cleanup + Docs)       ← Aufraeuemn
```

Geschaetzter Aufwand: Tasks 1-6 = Code (2-3h), Tasks 7-9 = Verifizierung (1h), Task 10 = Cleanup (30min)

---

## R1 Checkpoints (NICHT RATEN)

An diesen Stellen MUSS die Doku gelesen werden:

| Checkpoint | Doku-Quelle |
|-----------|-------------|
| Gateway Config Format | `docs/references/openclaw-nemoclaw-reference.md` Section 2 |
| Plugin Entry Point | `docs/references/openclaw-nemoclaw-reference.md` Section 3 |
| Plugin Volume Mount Pfad | `docs/references/openclaw-nemoclaw-reference.md` Section 4 |
| Health Check Endpoint | `docs/references/openclaw-nemoclaw-reference.md` Section 2 |
| Gateway Plugin Loading | Gateway Logs lesen, nicht raten |
