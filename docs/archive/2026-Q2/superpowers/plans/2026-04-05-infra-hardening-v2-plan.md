# NomOS Infrastructure Hardening v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vault mandatory with auto-init, First-Time Setup Wizard, 40 E2E tests, structured JSON logging. No compromises.

**Architecture:** vault-init as Docker init-service generates and seeds secrets on first run. Console Setup Wizard guides user through unseal key, admin account, 2FA, LLM provider. Structured JSON logging with request correlation IDs across all services. Playwright + API integration tests against running Docker stack in CI.

**Tech Stack:** HashiCorp Vault 1.17, FastAPI, Next.js 15, Playwright, pytest, Docker Compose

**Spec:** `docs/superpowers/specs/2026-04-05-infra-hardening-v2-design.md`

---

## Plan Structure

This plan is split into 3 sub-plans that build on each other:

| Sub-Plan | Phase | Tasks | Estimated |
|----------|-------|-------|-----------|
| **Plan 1: Vault + Setup Wizard** | A+B | 8 Tasks | ~10h |
| **Plan 2: Structured Logging** | C | 4 Tasks | ~4h |
| **Plan 3: E2E Test Suite** | D+E | 5 Tasks | ~6h |

**Dependency:** Plan 2 and Plan 3 can be started after Plan 1 is complete. Plan 2 and Plan 3 are independent of each other.

---

# PLAN 1: Vault Mandatory + Setup Wizard

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `vault/init-entrypoint.sh` | Vault-init service script (replaces current init.sh) |
| `nomos-api/nomos_api/routers/system.py` | GET /api/system/status, GET /api/system/unseal-key |
| `nomos-api/tests/test_system_status.py` | Tests for system status endpoint |
| `nomos-api/tests/test_vault_ttl_cache.py` | Tests for TTL cache |
| `nomos-console/src/app/setup/page.tsx` | First-Time Setup Wizard (4 steps) |
| `nomos-console/src/app/setup/layout.tsx` | Setup layout (no sidebar) |

### Modified Files

| File | Changes |
|------|---------|
| `docker-compose.yml` | Add vault-init service, nomos-vault-init volume, API reads creds from volume |
| `nomos-api/nomos_api/vault_client.py` | Add TTL cache (60s) |
| `nomos-api/nomos_api/vault_source.py` | Read AppRole creds from shared volume if ENV empty |
| `nomos-api/nomos_api/config.py` | Remove required secrets (jwt_secret etc), Vault generates them |
| `nomos-api/nomos_api/routers/auth.py` | Password min 12 chars validation |
| `nomos-api/nomos_api/main.py` | Add system router |
| `nomos-console/src/lib/api.ts` | Setup redirect logic |
| `nomos-console/src/lib/i18n/de.ts` | Setup wizard translations |
| `nomos-console/src/lib/i18n/en.ts` | Setup wizard translations |
| `.env.example` | Reduce to DB_PASSWORD + optional LLM key |
| `.github/workflows/ci.yml` | Add vault-init to docker-build step |

---

### Task 1: vault-init Docker Service

**Files:**
- Create: `vault/init-entrypoint.sh`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create vault-init entrypoint script**

Create `vault/init-entrypoint.sh` — idempotent init script that:
1. Waits for Vault healthy
2. If not initialized: init, unseal, enable KV v2, create AppRole, generate system secrets, seed into Vault
3. If already initialized: read unseal key, unseal, verify AppRole creds
4. Write AppRole creds to shared volume `/vault/init/approle-creds.env`
5. Exit 0

The script must generate system secrets (jwt_secret, plugin_api_key, gateway_token) using `openssl rand` and store them in Vault at `nomos/secrets/system`. DB password comes from ENV and is stored at `nomos/secrets/database`.

- [ ] **Step 2: Add vault-init service to docker-compose.yml**

Add after vault service:
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
      - ./vault/init-entrypoint.sh:/vault/init-entrypoint.sh:ro
    environment:
      - VAULT_ADDR=http://vault:8200
      - NOMOS_DB_PASSWORD=${NOMOS_DB_PASSWORD:?Set NOMOS_DB_PASSWORD in .env}
    entrypoint: ["/bin/sh", "/vault/init-entrypoint.sh"]
    restart: "no"
```

Add volume `nomos-vault-init:` to volumes section.

Change nomos-api depends_on: add `vault-init: condition: service_completed_successfully`.

Mount init volume in nomos-api: `- nomos-vault-init:/vault/init:ro`

Same for nomos-worker.

- [ ] **Step 3: Test vault-init locally**

```bash
docker compose down -v
docker compose up -d vault
docker compose up vault-init
# Should show: "Vault initialized", "AppRole credentials written"
cat /tmp/test-vault-init  # or docker volume inspect
docker compose down -v
```

- [ ] **Step 4: Commit**

```bash
git add vault/init-entrypoint.sh docker-compose.yml
git commit -m "feat(vault): vault-init service — auto-init, auto-unseal, secret generation"
```

---

### Task 2: VaultClient TTL Cache

**Files:**
- Modify: `nomos-api/nomos_api/vault_client.py`
- Create: `nomos-api/tests/test_vault_ttl_cache.py`

- [ ] **Step 1: Write TTL cache tests**

```python
# nomos-api/tests/test_vault_ttl_cache.py
import time
from unittest.mock import MagicMock, patch
from nomos_api.vault_client import VaultClient

class TestTTLCache:
    def _make_client(self):
        with patch("nomos_api.vault_client.hvac.Client") as mock_cls:
            mock_hvac = MagicMock()
            mock_cls.return_value = mock_hvac
            mock_hvac.is_authenticated.return_value = True
            client = VaultClient(
                addr="http://vault:8200",
                role_id="test",
                secret_id="test",
                cache_ttl=0.5,  # 500ms for test speed
            )
            return client, mock_hvac

    def test_cache_hit_within_ttl(self):
        client, mock_hvac = self._make_client()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        # First read — cache miss
        result1 = client.get_secret("test/path")
        assert result1 == {"key": "value"}
        # Second read — cache hit (no Vault call)
        mock_hvac.secrets.kv.v2.read_secret_version.reset_mock()
        result2 = client.get_secret("test/path")
        assert result2 == {"key": "value"}
        mock_hvac.secrets.kv.v2.read_secret_version.assert_not_called()

    def test_cache_miss_after_ttl(self):
        client, mock_hvac = self._make_client()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "old"}}
        }
        client.get_secret("test/path")
        # Wait for TTL to expire
        time.sleep(0.6)
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "new"}}
        }
        result = client.get_secret("test/path")
        assert result == {"key": "new"}

    def test_cache_fallback_on_error_within_ttl(self):
        client, mock_hvac = self._make_client()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "cached"}}
        }
        client.get_secret("test/path")
        # Vault goes down
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("down")
        result = client.get_secret("test/path")
        assert result == {"key": "cached"}  # Still returns cached
```

- [ ] **Step 2: Run tests — expect fail**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-api && python -m pytest tests/test_vault_ttl_cache.py -v`
Expected: FAIL (cache_ttl parameter doesn't exist yet)

- [ ] **Step 3: Implement TTL cache in VaultClient**

Modify `vault_client.py`:
- Add `cache_ttl: float = 60.0` parameter to `__init__`
- Change `_cache` type to `dict[str, tuple[dict, float]]` (value + timestamp)
- In `get_secret()`: check timestamp, return cached if within TTL
- On Vault read success: update cache with `(data, time.time())`
- On Vault read failure: return cached value regardless of TTL (degraded mode)

- [ ] **Step 4: Run tests — expect pass**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-api && python -m pytest tests/test_vault_ttl_cache.py tests/test_vault_client.py -v`
Expected: ALL PASS (new + existing tests)

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/vault_client.py nomos-api/tests/test_vault_ttl_cache.py
git commit -m "feat(vault): TTL cache (60s) — reduces Vault load, graceful degradation"
```

---

### Task 3: Config reads secrets from Vault, not ENV

**Files:**
- Modify: `nomos-api/nomos_api/config.py`
- Modify: `nomos-api/nomos_api/vault_source.py`
- Modify: `.env.example`

- [ ] **Step 1: Update vault_source.py to read AppRole creds from shared volume**

Add to `_get_vault_client()`: before checking ENV, try reading from `/vault/init/approle-creds.env` file. If file exists and contains VAULT_ROLE_ID/VAULT_SECRET_ID, use those. ENV overrides file.

- [ ] **Step 2: Update VAULT_FIELD_MAP for new Vault paths**

The vault-init script stores secrets at:
- `nomos/secrets/system` → `{jwt_secret, plugin_api_key, gateway_token}`
- `nomos/secrets/database` → `{password}`
- `nomos/secrets/llm_keys` → `{nvidia_api_key, openai_api_key, anthropic_api_key}`

Update the field map accordingly.

- [ ] **Step 3: Make secret fields optional with Vault-generated defaults**

In `config.py`, change:
```python
# FROM:
jwt_secret: str      # Required, no default
plugin_api_key: str  # Required, no default
gateway_token: str   # Required, no default
db_password: str     # Required, no default

# TO:
jwt_secret: str = "vault-pending"       # Vault will override
plugin_api_key: str = "vault-pending"   # Vault will override
gateway_token: str = "vault-pending"    # Vault will override
db_password: str = ""                   # From ENV (for postgres container)
```

Update `validate_settings()` to also reject `"vault-pending"` in production mode.

- [ ] **Step 4: Update .env.example**

Reduce to minimal:
```env
# NomOS — Only 1 required field. Vault generates everything else.
NOMOS_DB_PASSWORD=your_secure_password_here

# LLM Provider (optional here, can configure via Console later)
# NVIDIA_API_KEY=nvapi-...

# Runtime
NOMOS_DEV_MODE=false
NOMOS_DOMAIN=localhost
```

- [ ] **Step 5: Run all tests**

```bash
cd /c/Users/Legion/Documents/nomos/nomos-api && python -m pytest tests/ -q --ignore=tests/test_auth_router.py --ignore=tests/test_rate_limiter.py
```
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add nomos-api/nomos_api/config.py nomos-api/nomos_api/vault_source.py .env.example
git commit -m "feat(config): secrets from Vault, .env reduced to DB_PASSWORD only"
```

---

### Task 4: System Status Endpoint

**Files:**
- Create: `nomos-api/nomos_api/routers/system.py`
- Create: `nomos-api/tests/test_system_status.py`
- Modify: `nomos-api/nomos_api/main.py`

- [ ] **Step 1: Write tests for system status**

```python
# nomos-api/tests/test_system_status.py
import pytest

class TestSystemStatus:
    async def test_status_before_setup(self, client):
        """Fresh system: no admin, setup required."""
        resp = await client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["setup_required"] is True
        assert data["admin_exists"] is False

    async def test_status_after_bootstrap(self, client):
        """After admin bootstrap: setup no longer required."""
        await client.post("/api/users/bootstrap", json={
            "email": "admin@test.com", "password": "SecureP@ssw0rd12!"
        })
        resp = await client.get("/api/system/status")
        data = resp.json()
        assert data["setup_required"] is False
        assert data["admin_exists"] is True

    async def test_unseal_key_only_once(self, client):
        """Unseal key endpoint returns 410 after first read."""
        # First call — returns key (or mock)
        resp1 = await client.get("/api/system/unseal-key")
        # For tests without real Vault, expect 404 or mock
        assert resp1.status_code in (200, 404)
        # After first read, should be gone
        if resp1.status_code == 200:
            resp2 = await client.get("/api/system/unseal-key")
            assert resp2.status_code == 410
```

- [ ] **Step 2: Implement system router**

Create `nomos-api/nomos_api/routers/system.py`:
- `GET /api/system/status` → checks if admin user exists in DB, vault status
- `GET /api/system/unseal-key` → reads unseal key from `/vault/init/unseal-key` file, returns it ONCE, then deletes from memory (not from file — that's for auto-unseal)
- Both endpoints are PUBLIC (no auth required — needed before login exists)

- [ ] **Step 3: Register router in main.py**

Add `from nomos_api.routers import system` and `app.include_router(system.router)`.
Add `/api/system/status` and `/api/system/unseal-key` to `PUBLIC_PATHS`.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_system_status.py -v
```
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/routers/system.py nomos-api/tests/test_system_status.py nomos-api/nomos_api/main.py
git commit -m "feat(api): system status endpoint — setup_required, admin_exists, unseal-key"
```

---

### Task 5: Password Validation (min 12 chars, complexity)

**Files:**
- Modify: `nomos-api/nomos_api/routers/auth.py`
- Modify: `nomos-api/nomos_api/schemas.py`
- Create: `nomos-api/tests/test_password_validation.py`

- [ ] **Step 1: Write password validation tests**

```python
# nomos-api/tests/test_password_validation.py
import pytest
from nomos_api.schemas import validate_password_strength

class TestPasswordValidation:
    def test_too_short(self):
        with pytest.raises(ValueError, match="12"):
            validate_password_strength("Short1!")

    def test_no_uppercase(self):
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_strength("alllowercase1!")

    def test_no_lowercase(self):
        with pytest.raises(ValueError, match="lowercase"):
            validate_password_strength("ALLUPPERCASE1!")

    def test_no_digit(self):
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength("NoDigitsHere!")

    def test_no_special(self):
        with pytest.raises(ValueError, match="special"):
            validate_password_strength("NoSpecialChar1")

    def test_valid_password(self):
        assert validate_password_strength("SecureP@ssw0rd12!") is None
```

- [ ] **Step 2: Implement validation function in schemas.py**

Add `validate_password_strength(password: str) -> None` that raises `ValueError` with human-readable message for each rule violation. Apply as Pydantic field_validator on bootstrap and user creation.

- [ ] **Step 3: Run tests**

Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add nomos-api/nomos_api/schemas.py nomos-api/nomos_api/routers/auth.py nomos-api/tests/test_password_validation.py
git commit -m "feat(auth): password validation — min 12 chars, upper/lower/digit/special"
```

---

### Task 6: Setup Wizard — Console Frontend

**Files:**
- Create: `nomos-console/src/app/setup/page.tsx`
- Create: `nomos-console/src/app/setup/layout.tsx`
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-console/src/lib/i18n/en.ts`
- Modify: `nomos-console/src/app/login/page.tsx` (redirect to /setup if needed)

- [ ] **Step 1: Add i18n keys for Setup Wizard**

Add ~40 keys for the 4 wizard steps (titles, descriptions, labels, buttons, warnings) in both de.ts and en.ts. All German text with proper umlauts.

- [ ] **Step 2: Create setup layout (no sidebar)**

`setup/layout.tsx` — full-screen layout without the admin sidebar. Just NomOS logo + centered content.

- [ ] **Step 3: Create setup page with 4 steps**

`setup/page.tsx`:
- Step 1: Unseal key display (fetch from `/api/system/unseal-key`, copy button, PDF download, checkbox)
- Step 2a: Admin account (email, password with strength indicator, recovery key display, checkbox)
- Step 2b: Optional 2FA (QR code, TOTP verify)
- Step 3: LLM Provider (NVIDIA/OpenAI/Anthropic key input, test button)
- Step 4: Summary + "Start NomOS" button

On mount: fetch `/api/system/status`. If `setup_required === false`, redirect to `/login`.

- [ ] **Step 4: Modify login page to check setup status**

In `login/page.tsx`: before rendering login form, fetch `/api/system/status`. If `setup_required === true`, redirect to `/setup`.

- [ ] **Step 5: Run console tests**

```bash
cd /c/Users/Legion/Documents/nomos/nomos-console && npx vitest run
```
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add nomos-console/src/app/setup/ nomos-console/src/lib/i18n/ nomos-console/src/app/login/page.tsx
git commit -m "feat(console): First-Time Setup Wizard — unseal key, admin, 2FA, LLM provider"
```

---

### Task 7: Docker Compose Integration (vault-init → API → Console)

**Files:**
- Modify: `docker-compose.yml`
- Modify: `nomos-api/Dockerfile`
- Modify: `.env`

- [ ] **Step 1: Update docker-compose.yml**

Remove NOMOS_JWT_SECRET, NOMOS_PLUGIN_API_KEY, NOMOS_GATEWAY_TOKEN from nomos-api environment (Vault provides them). Keep NOMOS_DB_PASSWORD (PostgreSQL needs it).

Add volume mount for vault-init output: `nomos-vault-init:/vault/init:ro` on nomos-api and nomos-worker.

Ensure dependency chain: vault → vault-init → nomos-api → nomos-console → caddy.

- [ ] **Step 2: Update .env for new minimal format**

Only NOMOS_DB_PASSWORD + optional LLM keys.

- [ ] **Step 3: Full stack test**

```bash
docker compose down -v
docker compose build
docker compose up -d
sleep 60
docker ps  # 9/9 healthy (vault-init exits 0)
curl -sf http://localhost:8060/api/system/status  # setup_required: true
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml nomos-api/Dockerfile .env.example
git commit -m "feat(docker): vault-init → API → Console dependency chain, minimal .env"
```

---

### Task 8: Plan 1 Integration Test

**Files:** None (verification only)

- [ ] **Step 1: Fresh start**

```bash
docker compose down -v
docker compose up -d
sleep 90
docker ps  # All healthy, vault-init exited
```

- [ ] **Step 2: Check system status**

```bash
curl -sf http://localhost:8060/api/system/status
# Expected: {"setup_required": true, "admin_exists": false, "vault_status": "healthy"}
```

- [ ] **Step 3: Browser test — Setup Wizard**

Open http://localhost:3040 → should redirect to /setup
Step through wizard: unseal key → admin → 2FA (skip) → LLM key → done
Should redirect to dashboard.

- [ ] **Step 4: Verify Vault has secrets**

```bash
docker exec nomos-vault-1 sh -c 'export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=$(cat /vault/file/init-output.json | jq -r .root_token) && vault kv get nomos/secrets/system'
# Should show jwt_secret, plugin_api_key, gateway_token
```

- [ ] **Step 5: Restart and verify auto-unseal**

```bash
docker compose restart
sleep 60
curl -sf http://localhost:8060/health  # healthy, vault: healthy
```

- [ ] **Step 6: Commit**

```bash
git commit --allow-empty -m "test: Plan 1 integration test passed — vault-init + setup wizard verified"
```

---

# PLAN 2: Structured Logging + Error Standard

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `nomos-api/nomos_api/middleware/logging.py` | JSON structured logging middleware |
| `nomos-api/nomos_api/middleware/request_id.py` | X-Request-ID generation + propagation |
| `nomos-api/nomos_api/errors.py` | Standardized error response schema |
| `nomos-api/tests/test_structured_logging.py` | Logging format tests |
| `nomos-api/tests/test_error_responses.py` | Error format tests |

### Modified Files

| File | Changes |
|------|---------|
| `nomos-api/nomos_api/main.py` | Replace BasicConfig with JSON logger, add request-ID middleware |
| `nomos-api/nomos_api/routers/health.py` | Extended health with component status |
| `nomos-console/src/lib/api.ts` | Send X-Request-ID header |

---

### Task 9: JSON Structured Logging

**Files:**
- Create: `nomos-api/nomos_api/middleware/logging.py`
- Create: `nomos-api/nomos_api/middleware/__init__.py`
- Create: `nomos-api/tests/test_structured_logging.py`
- Modify: `nomos-api/nomos_api/main.py`

- [ ] **Step 1: Write logging tests**

Test that log output is valid JSON with required fields: timestamp, level, logger, message, request_id.

- [ ] **Step 2: Implement JSON logging middleware**

Replace `logging.basicConfig(format="%(asctime)s [%(levelname)s]...")` with a JSON formatter. Use `python-json-logger` or custom `logging.Formatter`. Every log entry includes: timestamp, level, logger, message. Request-scoped fields (request_id, method, path, status, duration_ms) added by middleware.

- [ ] **Step 3: Run tests + verify output**

```bash
docker compose up -d nomos-api
docker logs nomos-nomos-api-1 | python -m json.tool  # Should be valid JSON
```

- [ ] **Step 4: Commit**

---

### Task 10: Request Correlation ID

**Files:**
- Create: `nomos-api/nomos_api/middleware/request_id.py`
- Modify: `nomos-console/src/lib/api.ts`

- [ ] **Step 1: Implement X-Request-ID middleware**

If client sends `X-Request-ID` header, use it. Otherwise generate UUID. Store in request.state. Include in all log entries. Include in response headers.

- [ ] **Step 2: Frontend sends X-Request-ID**

In `api.ts`, generate UUID for each request and include as header. Store last request_id for error reporting.

- [ ] **Step 3: Commit**

---

### Task 11: Standardized Error Responses

**Files:**
- Create: `nomos-api/nomos_api/errors.py`
- Create: `nomos-api/tests/test_error_responses.py`
- Modify: `nomos-api/nomos_api/main.py`

- [ ] **Step 1: Define error response schema**

```python
class NomOSError(BaseModel):
    detail: str           # Human-readable DE or EN
    code: str             # Machine-readable: AGENT_NOT_FOUND, AUTH_FAILED, etc.
    request_id: str       # From X-Request-ID

# Global exception handler catches all HTTPExceptions and wraps in this format
```

- [ ] **Step 2: Add global exception handler**

In `main.py`, add `@app.exception_handler(HTTPException)` that wraps every error in the standard format. Add `@app.exception_handler(Exception)` for unexpected errors (500 with code `INTERNAL_ERROR`).

- [ ] **Step 3: Test that no endpoint returns a naked error**

Run through all error scenarios and verify format.

- [ ] **Step 4: Commit**

---

### Task 12: Extended Health Endpoint

**Files:**
- Modify: `nomos-api/nomos_api/routers/health.py`
- Modify: `nomos-api/nomos_api/schemas.py`

- [ ] **Step 1: Extend HealthResponse with components**

```python
class HealthComponentStatus(BaseModel):
    vault: str       # healthy, degraded, unavailable, not_configured
    postgres: str    # healthy, unavailable
    valkey: str      # healthy, unavailable
    gateway: str     # online, offline
    worker: str      # healthy, unavailable

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    vault: str | None = None  # Backwards compat
    components: HealthComponentStatus | None = None
    uptime_seconds: int | None = None
```

- [ ] **Step 2: Implement component health checks**

PostgreSQL: try DB query. Valkey: try ping. Gateway: try /healthz. Worker: check ARQ job queue.

- [ ] **Step 3: Test + Commit**

---

# PLAN 3: E2E Test Suite

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `nomos-console/e2e/setup-wizard.spec.ts` | Setup wizard E2E |
| `nomos-console/e2e/login-errors.spec.ts` | Login error cases |
| `nomos-console/e2e/hire-and-chat.spec.ts` | Complete hire-to-chat flow |
| `nomos-console/e2e/settings-persist.spec.ts` | Settings persistence |
| `nomos-console/e2e/rbac.spec.ts` | Multi-user RBAC |
| `nomos-console/e2e/agent-lifecycle.spec.ts` | Pause/resume/compliance |
| `nomos-console/e2e/error-handling.spec.ts` | Infrastructure failure cases |
| `nomos-console/e2e/security.spec.ts` | XSS, injection, headers |
| `nomos-api/tests/integration/test_api_e2e.py` | API integration tests |
| `nomos-api/tests/integration/conftest.py` | Docker-based test fixtures |

### Modified Files

| File | Changes |
|------|---------|
| `nomos-console/playwright.config.ts` | Docker-based base URL, retries |
| `.github/workflows/ci.yml` | Add e2e-test job |

---

### Task 13: Playwright Setup for Docker

**Files:**
- Modify: `nomos-console/playwright.config.ts`
- Create: `nomos-console/e2e/global-setup.ts`

- [ ] **Step 1: Configure Playwright for Docker stack**

Base URL: `http://localhost:3040`. Global setup: wait for health endpoint. Retries: 2. Screenshots on failure.

- [ ] **Step 2: Global setup — wait for stack healthy**

`global-setup.ts`: poll `http://localhost:8060/health` until 200, max 120s. Poll `http://localhost:3040` until 200. Then check `/api/system/status` for setup state.

- [ ] **Step 3: Commit**

---

### Task 14: Playwright Browser Tests (20 scenarios)

**Files:**
- Create: 8 spec files as listed above

- [ ] **Step 1: Happy path tests (1-10)**

Write tests for: login, hire wizard, chat, settings, pause/resume, compliance tab, audit trail, RBAC, admin audit, diagnostics.

Each test uses Playwright's `page.goto()`, `page.fill()`, `page.click()`, `expect()`.

- [ ] **Step 2: Error case tests (11-16)**

Wrong password, expired session, duplicate hire, chat while paused, empty message, no provider.

- [ ] **Step 3: Infrastructure failure tests (17-20)**

API offline, gateway offline, vault offline, concurrent chat.

Use `docker compose stop <service>` in test to simulate failures.

- [ ] **Step 4: Run all Playwright tests**

```bash
cd /c/Users/Legion/Documents/nomos
docker compose up -d
cd nomos-console && npx playwright test
```
Expected: 20/20 pass

- [ ] **Step 5: Commit**

---

### Task 15: API Integration Tests (20 scenarios)

**Files:**
- Create: `nomos-api/tests/integration/test_api_e2e.py`
- Create: `nomos-api/tests/integration/conftest.py`

- [ ] **Step 1: Create integration test fixtures**

`conftest.py`: HTTP client pointing at `http://localhost:8060`. Login helper. Agent creation helper. Marked with `@pytest.mark.integration` so they don't run in unit test suite.

- [ ] **Step 2: Write 20 API integration tests**

Functional (8), Error/Edge (8), Security (4) as defined in spec.

- [ ] **Step 3: Run integration tests**

```bash
cd /c/Users/Legion/Documents/nomos/nomos-api
python -m pytest tests/integration/ -v -m integration
```
Expected: 20/20 pass

- [ ] **Step 4: Commit**

---

### Task 16: CI Pipeline Integration

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add e2e-test job**

```yaml
e2e-test:
  name: E2E Tests (Docker Stack)
  runs-on: ubuntu-latest
  needs: docker-build
  steps:
    - uses: actions/checkout@v4
    - run: echo "NOMOS_DB_PASSWORD=ci-test-pw" > .env
    - run: docker compose up -d
    - run: sleep 90
    - run: docker ps --format "table {{.Names}}\t{{.Status}}"
    - uses: actions/setup-node@v4
      with:
        node-version: "22"
    - run: cd nomos-console && npm ci && npx playwright install chromium
    - run: cd nomos-console && npx playwright test
    - run: cd nomos-api && python -m pytest tests/integration/ -v -m integration
    - run: docker compose down -v
    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: playwright-report
        path: nomos-console/playwright-report/
```

- [ ] **Step 2: Update ci-summary to include E2E**

- [ ] **Step 3: Commit**

---

### Task 17: Final Integration Test

- [ ] **Step 1: Fresh stack, complete flow**

```bash
docker compose down -v
docker compose up -d
# Wait for healthy
# Setup Wizard in browser
# Hire agent, chat, verify
# Check structured logs: docker logs nomos-nomos-api-1 | jq
# Check error format: curl with bad request
# Check security headers
# Run Playwright: npx playwright test
# Run API integration: pytest tests/integration/
```

- [ ] **Step 2: All 40 E2E tests green**

- [ ] **Step 3: Final commit**

```bash
git commit --allow-empty -m "test: infra hardening v2 complete — vault, wizard, logging, 40 E2E tests"
```

---

## Dependencies

```
Plan 1:
  Task 1 (vault-init) → Task 2 (TTL cache) → Task 3 (config from Vault)
  Task 4 (system status) → Task 5 (password validation) → Task 6 (setup wizard)
  Task 3 + Task 6 → Task 7 (docker integration) → Task 8 (integration test)

Plan 2 (after Plan 1):
  Task 9 (JSON logging) → Task 10 (request-ID) → Task 11 (error standard)
  Task 11 → Task 12 (health extended)

Plan 3 (after Plan 1, parallel with Plan 2):
  Task 13 (playwright setup) → Task 14 (browser tests)
  Task 15 (API integration tests)
  Task 14 + Task 15 → Task 16 (CI) → Task 17 (final test)
```
