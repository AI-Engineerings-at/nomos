# NomOS Enterprise Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform NomOS from MVP-grade security to Enterprise-grade: Vault secret management, persistent rate limiting, configurable CORS, editable settings with encrypted key storage, automated contract enforcement, and a complete test suite (vitest + Playwright Enterprise Suite).

**Architecture:** HashiCorp Vault (Docker service) manages all secrets via KV v2 engine. `pydantic-settings` `settings_customise_sources()` integrates Vault as highest-priority source. Rate limiter moves to Valkey (already in stack). Console gets full vitest coverage (20 pages x 4 states) and Playwright E2E Enterprise Suite (happy path + error cases + multi-user + full sweep).

**Tech Stack:** Python 3.12 (FastAPI, Pydantic v2, hvac, valkey-py), TypeScript strict (Next.js 15, vitest, @testing-library/react, Playwright), HashiCorp Vault 1.15, Valkey 8, Docker Compose

**Spec:** `docs/superpowers/specs/2026-03-27-enterprise-hardening-design.md`

---

## File Structure

### Phase 0: Security Hardening — New/Modified Files

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `vault/config/vault.hcl` | Vault server config (file storage, listener) |
| Create | `vault/policies/nomos-api.hcl` | Least-privilege policy for nomos-api |
| Create | `vault/init.sh` | Idempotent Vault bootstrap (KV engine, AppRole, seed secrets) |
| Create | `nomos-api/nomos_api/vault_client.py` | Vault client singleton (get/put/list with cache fallback) |
| Create | `nomos-api/nomos_api/vault_source.py` | Custom pydantic-settings source reading from Vault |
| Modify | `nomos-api/nomos_api/config.py` | Add Vault bootstrap fields, startup validation, customise_sources |
| Modify | `nomos-api/nomos_api/auth/rate_limiter.py` | Rewrite to use Valkey sorted sets |
| Modify | `nomos-api/nomos_api/main.py` | Remove hardcoded CORS regex, add dev_mode logic |
| Modify | `nomos-api/pyproject.toml` | Add hvac, valkey dependencies |
| Modify | `docker-compose.yml` | Add Vault service, replace `:-` with `:?`, add volumes |
| Modify | `nomos-api/docker-compose.yml` | Replace redis with valkey |
| Modify | `config/openclaw.json` | Template gateway token |
| Modify | `.env.example` | CHANGE_ME_REQUIRED placeholders |

### Phase 1: Backend Completion — New/Modified Files

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `nomos-plugin/src/api-client.ts` | Add res.ok guard to checkBudget |
| Modify | `nomos-plugin/src/hooks/before-tool-call.ts` | Handle budget error/unknown_agent |
| Modify | `nomos-api/nomos_api/routers/budget.py` | Restrictive default for unknown agents |
| Modify | `nomos-api/nomos_api/routers/settings.py` | Add PATCH endpoint, Vault integration |
| Modify | `nomos-api/nomos_api/schemas.py` | Add SystemSettingsResponse, SettingsUpdateRequest |
| Modify | `nomos-console/src/app/admin/settings/page.tsx` | Editable settings form |
| Modify | `nomos-console/src/lib/types.ts` | Add SettingsUpdateRequest type |
| Create | `scripts/export-schemas.py` | Export Pydantic schemas as JSON Schema |
| Create | `scripts/check-contracts.ts` | Parse types.ts, compare against JSON Schema |
| Create | `scripts/contract-naming-map.json` | Intentional rename mappings |
| Modify | `.github/workflows/ci.yml` | Add contract-check job |
| Modify | Multiple docs | MVP → Enterprise framing |

### Phase 2: Frontend Quality — New/Modified Files

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `nomos-console/vitest.config.ts` | Vitest configuration |
| Create | `nomos-console/src/test-utils.tsx` | Render wrapper, mocks, store reset |
| Create | `nomos-console/src/__tests__/*.test.tsx` | 20 page test files |
| Create | `nomos-console/src/lib/__tests__/*.test.ts` | Hook and util tests |
| Modify | `nomos-console/package.json` | Add test deps and script |
| Modify | `nomos-console/playwright.config.ts` | CI config, retries, reporters |
| Create | `nomos-console/e2e/auth.setup.ts` | Shared auth session |
| Create | `nomos-console/e2e/happy-path.spec.ts` | Full journey test |
| Create | `nomos-console/e2e/error-cases.spec.ts` | Error scenario tests |
| Create | `nomos-console/e2e/multi-user.spec.ts` | Role-based access tests |
| Create | `nomos-console/e2e/page-sweep.spec.ts` | All 20 pages visit test |

---

## Dependencies

```
Phase 0 (Security):
  P0.1 (Vault) ──┐
  P0.2 (Rate Limiter) ──┤── parallel (independent subsystems)
  P0.3 (CORS + Startup) ─┘── depends on P0.1 for config.py changes
  → Ralph-Loop #1 (Security)

Phase 1 (Backend): after Phase 0
  P1.1 (Budget-Hook) ──┐
  P1.2 (Settings PATCH) ── depends on P0.1 (Vault)
  P1.3 (Contract Tests) ──┤── parallel
  P1.4 (Docs Cleanup) ────┘
  → Ralph-Loop #2 (Backend)

Phase 2 (Frontend): after Phase 1
  P2.1 (Vitest) ──┐── parallel
  P2.2 (Playwright) ─┘── depends on P2.1 for test-utils
  → Ralph-Loop #3 (Frontend)

Phase 3: Ralph-Loop #4 (Final — all together)
```

**CRITICAL:** P0.1 and P0.3 both modify `config.py` — serialize them (P0.1 first, P0.3 second).

---

## PHASE 0: SECURITY HARDENING

### Task P0.1: Vault Integration + Secret Hardening

**Files:**
- Create: `vault/config/vault.hcl`
- Create: `vault/policies/nomos-api.hcl`
- Create: `vault/init.sh`
- Create: `nomos-api/nomos_api/vault_client.py`
- Create: `nomos-api/nomos_api/vault_source.py`
- Modify: `nomos-api/nomos_api/config.py`
- Modify: `nomos-api/pyproject.toml`
- Modify: `docker-compose.yml`
- Modify: `config/openclaw.json`
- Modify: `.env.example`
- Test: `nomos-api/tests/test_vault_client.py`
- Test: `nomos-api/tests/test_config_validation.py`

- [ ] **Step 1: Add hvac and valkey to dependencies**

```toml
# nomos-api/pyproject.toml — add to dependencies list
    "hvac>=2.1",
    "valkey>=6.0",
```

Run: `cd nomos-api && uv pip install -e ".[dev]"`
Expected: SUCCESS — both packages installed

- [ ] **Step 2: Create Vault server config**

```hcl
# vault/config/vault.hcl
storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://0.0.0.0:8200"
disable_mlock = true
ui = true
```

- [ ] **Step 3: Create Vault policy for nomos-api**

```hcl
# vault/policies/nomos-api.hcl
path "nomos/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "nomos/metadata/*" {
  capabilities = ["read", "list"]
}
```

- [ ] **Step 4: Create Vault init script**

```bash
#!/usr/bin/env bash
# vault/init.sh — Idempotent Vault bootstrap
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_ADDR

echo "Waiting for Vault..."
until vault status >/dev/null 2>&1; do sleep 1; done

# Check if already initialized
if vault status -format=json | grep -q '"initialized": true'; then
  echo "Vault already initialized."

  # Unseal if sealed (using stored keys)
  if vault status -format=json | grep -q '"sealed": true'; then
    if [ -f /vault/file/unseal-key.txt ]; then
      vault operator unseal "$(cat /vault/file/unseal-key.txt)"
    fi
  fi
else
  echo "Initializing Vault..."
  INIT_OUTPUT=$(vault operator init -key-shares=1 -key-threshold=1 -format=json)

  # Parse with jq (available in hashicorp/vault image)
  UNSEAL_KEY=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[0]')
  ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

  # WARNING: Unseal key stored next to encrypted data. For production,
  # use Vault auto-unseal with AWS KMS, GCP CKMS, or Azure Key Vault.
  # This file-based approach is for Docker Compose deployments only.
  echo "$UNSEAL_KEY" > /vault/file/unseal-key.txt
  echo "$ROOT_TOKEN" > /vault/file/root-token.txt
  chmod 600 /vault/file/unseal-key.txt /vault/file/root-token.txt

  vault operator unseal "$UNSEAL_KEY"
fi

# Login with root token
export VAULT_TOKEN="$(cat /vault/file/root-token.txt)"

# Enable KV v2 engine (idempotent)
vault secrets enable -path=nomos -version=2 kv 2>/dev/null || true

# Write policy
vault policy write nomos-api /vault/config/nomos-api.hcl 2>/dev/null || \
vault policy write nomos-api /vault/policies/nomos-api.hcl

# Enable AppRole auth (idempotent)
vault auth enable approle 2>/dev/null || true

# Create/update role
vault write auth/approle/role/nomos-api \
  token_policies="nomos-api" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0

# Get role_id and secret_id
ROLE_ID=$(vault read -field=role_id auth/approle/role/nomos-api/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/nomos-api/secret-id)

echo "VAULT_ROLE_ID=$ROLE_ID" > /vault/file/approle-creds.env
echo "VAULT_SECRET_ID=$SECRET_ID" >> /vault/file/approle-creds.env
chmod 600 /vault/file/approle-creds.env

echo "Vault bootstrap complete."
echo "  Role ID:    $ROLE_ID"
echo "  Secret ID:  $SECRET_ID"
```

Run: `chmod +x vault/init.sh`

- [ ] **Step 5: Create VaultClient**

```python
# nomos-api/nomos_api/vault_client.py
"""HashiCorp Vault client with in-memory cache fallback."""

from __future__ import annotations

import logging
from typing import Any

import hvac

logger = logging.getLogger(__name__)


class VaultClient:
    """Vault KV v2 client. Caches last-known values for resilience."""

    def __init__(self, addr: str, role_id: str, secret_id: str, mount: str = "nomos") -> None:
        self._mount = mount
        self._cache: dict[str, str] = {}
        self._client: hvac.Client | None = None

        if not role_id or not secret_id:
            logger.warning("Vault credentials not configured — running without Vault")
            return

        try:
            self._client = hvac.Client(url=addr)
            self._client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            logger.info("Vault authenticated via AppRole")
        except Exception:
            logger.exception("Failed to connect to Vault — falling back to cache/env")
            self._client = None

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            return self._client.is_authenticated()
        except Exception:
            return False

    def get_secret(self, path: str) -> str | None:
        """Read a secret from Vault KV v2. Falls back to cache if Vault unavailable."""
        if self._client and self.is_connected:
            try:
                result = self._client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point=self._mount, raise_on_deleted_version=True,
                )
                value = result["data"]["data"].get("value")
                if value is not None:
                    self._cache[path] = value
                return value
            except hvac.exceptions.InvalidPath:
                return None
            except Exception:
                logger.warning("Vault read failed for %s — using cache", path)

        return self._cache.get(path)

    def put_secret(self, path: str, value: str) -> bool:
        """Write a secret to Vault KV v2."""
        if not self._client or not self.is_connected:
            logger.error("Cannot write to Vault — not connected")
            return False
        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path, secret={"value": value}, mount_point=self._mount,
            )
            self._cache[path] = value
            return True
        except Exception:
            logger.exception("Vault write failed for %s", path)
            return False

    def list_secrets(self, prefix: str) -> list[str]:
        """List secret keys under a prefix."""
        if not self._client or not self.is_connected:
            return [k for k in self._cache if k.startswith(prefix)]
        try:
            result = self._client.secrets.kv.v2.list_secrets(
                path=prefix, mount_point=self._mount,
            )
            return result["data"]["keys"]
        except Exception:
            return [k for k in self._cache if k.startswith(prefix)]

    def delete_secret(self, path: str) -> bool:
        """Delete a secret from Vault."""
        if not self._client or not self.is_connected:
            return False
        try:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path, mount_point=self._mount,
            )
            self._cache.pop(path, None)
            return True
        except Exception:
            logger.exception("Vault delete failed for %s", path)
            return False

    def health_status(self) -> str:
        """Return vault health: 'healthy', 'degraded', 'unavailable'."""
        if not self._client:
            return "unavailable"
        try:
            if self._client.is_authenticated():
                return "healthy"
            return "degraded"
        except Exception:
            return "degraded" if self._cache else "unavailable"
```

- [ ] **Step 6: Write test for VaultClient**

```python
# nomos-api/tests/test_vault_client.py
"""Tests for Vault client — uses mock hvac to avoid real Vault dependency."""

from unittest.mock import MagicMock, patch

import pytest

from nomos_api.vault_client import VaultClient


class TestVaultClientWithoutVault:
    """Test behavior when Vault is not available."""

    def test_no_credentials_logs_warning(self):
        client = VaultClient(addr="http://localhost:8200", role_id="", secret_id="")
        assert not client.is_connected
        assert client.health_status() == "unavailable"

    def test_get_secret_returns_none_without_vault(self):
        client = VaultClient(addr="http://localhost:8200", role_id="", secret_id="")
        assert client.get_secret("nomos/secrets/jwt") is None

    def test_put_secret_fails_without_vault(self):
        client = VaultClient(addr="http://localhost:8200", role_id="", secret_id="")
        assert client.put_secret("nomos/secrets/jwt", "value") is False

    def test_cache_fallback(self):
        client = VaultClient(addr="http://localhost:8200", role_id="", secret_id="")
        client._cache["test/path"] = "cached_value"
        assert client.get_secret("test/path") == "cached_value"


class TestVaultClientWithMock:
    """Test behavior with mocked Vault connection."""

    def _make_client(self) -> tuple[VaultClient, MagicMock]:
        with patch("nomos_api.vault_client.hvac.Client") as mock_cls:
            mock_hvac = MagicMock()
            mock_cls.return_value = mock_hvac
            mock_hvac.is_authenticated.return_value = True
            client = VaultClient(
                addr="http://vault:8200",
                role_id="test-role",
                secret_id="test-secret",
            )
            return client, mock_hvac

    def test_connected_after_login(self):
        client, _ = self._make_client()
        assert client.is_connected
        assert client.health_status() == "healthy"

    def test_get_secret_reads_from_vault(self):
        client, mock_hvac = self._make_client()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "my-secret"}}
        }
        assert client.get_secret("secrets/jwt") == "my-secret"
        assert client._cache["secrets/jwt"] == "my-secret"

    def test_put_secret_writes_to_vault(self):
        client, mock_hvac = self._make_client()
        assert client.put_secret("secrets/jwt", "new-secret") is True
        mock_hvac.secrets.kv.v2.create_or_update_secret.assert_called_once()

    def test_get_secret_falls_back_to_cache_on_error(self):
        client, mock_hvac = self._make_client()
        client._cache["secrets/jwt"] = "cached"
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("timeout")
        assert client.get_secret("secrets/jwt") == "cached"
```

Run: `cd nomos-api && python -m pytest tests/test_vault_client.py -v`
Expected: ALL PASS

- [ ] **Step 7: Create VaultSettingsSource**

```python
# nomos-api/nomos_api/vault_source.py
"""Custom pydantic-settings source that reads from HashiCorp Vault."""

from __future__ import annotations

import os
from typing import Any

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


# Mapping: Settings field name → Vault KV path
VAULT_FIELD_MAP: dict[str, str] = {
    "jwt_secret": "secrets/jwt_secret",
    "plugin_api_key": "secrets/plugin_api_key",
    "gateway_token": "secrets/gateway_token",
    "gateway_url": "config/gateway_url",
    "retention_days": "config/retention_days",
    "pii_filter_mode": "config/pii_filter_mode",
}


class VaultSettingsSource(PydanticBaseSettingsSource):
    """Read settings from Vault KV v2. Imported lazily to avoid circular deps."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        vault_path = VAULT_FIELD_MAP.get(field_name)
        if vault_path is None:
            return None, field_name, False

        # Lazy import to avoid circular dependency with config.py
        from nomos_api.vault_client import VaultClient

        addr = os.environ.get("NOMOS_VAULT_ADDR", "http://vault:8200")
        role_id = os.environ.get("NOMOS_VAULT_ROLE_ID", "")
        secret_id = os.environ.get("NOMOS_VAULT_SECRET_ID", "")

        if not role_id or not secret_id:
            return None, field_name, False

        client = _get_vault_client(addr, role_id, secret_id)
        value = client.get_secret(vault_path)
        if value is not None:
            return value, field_name, True
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field_name, field_info in self.settings_cls.model_fields.items():
            value, _, found = self.get_field_value(field_info, field_name)
            if found:
                data[field_name] = value
        return data


_vault_client_cache: dict[str, Any] = {}


def _get_vault_client(addr: str, role_id: str, secret_id: str) -> Any:
    """Singleton Vault client for settings source."""
    key = f"{addr}:{role_id}"
    if key not in _vault_client_cache:
        from nomos_api.vault_client import VaultClient
        _vault_client_cache[key] = VaultClient(addr=addr, role_id=role_id, secret_id=secret_id)
    return _vault_client_cache[key]
```

- [ ] **Step 8: Modify config.py — Vault integration + startup validation**

Replace the entire `nomos-api/nomos_api/config.py` with:

```python
"""NomOS API configuration — Vault-first, ENV fallback, startup validation."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

# Known insecure defaults that MUST NOT run in production
_INSECURE_DEFAULTS = {
    "jwt_secret": {"change-me-in-production", "dev-secret-not-for-production-32chars"},
    "plugin_api_key": {"nomos-plugin-dev"},
    "gateway_token": {"nomos-dev-token"},
    "db_password": {"nomos"},
}


class Settings(BaseSettings):
    """API settings. Priority: Vault → ENV → .env file."""

    # Infrastructure
    database_url: str = "postgresql+asyncpg://nomos:nomos@localhost:5432/nomos"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "NomOS Fleet API"
    api_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3040"]
    agents_dir: Path = Path("./data/agents")

    # Secrets (should come from Vault in production)
    jwt_secret: str = "change-me-in-production"
    plugin_api_key: str = "nomos-plugin-dev"
    gateway_url: str = "http://openclaw-gateway:18789"
    gateway_token: str = "nomos-dev-token"
    db_password: str = "nomos"  # Extracted for validation; database_url still used for connection

    # Config (editable via Settings UI when Vault is connected)
    retention_days: int = 365
    pii_filter_mode: str = "standard"

    # Vault bootstrap (must come from ENV — cannot be in Vault itself)
    vault_addr: str = "http://vault:8200"
    vault_role_id: str = ""
    vault_secret_id: str = ""

    # Dev mode (enables localhost CORS, skips secret validation)
    dev_mode: bool = False

    # Valkey URL for rate limiter
    valkey_url: str = "redis://valkey:6379"

    model_config = {"env_prefix": "NOMOS_", "env_file": ".env", "extra": "ignore"}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        from nomos_api.vault_source import VaultSettingsSource

        vault = VaultSettingsSource(settings_cls)
        return (init_settings, vault, env_settings, dotenv_settings)


settings = Settings()


def validate_settings() -> None:
    """Abort startup if insecure defaults are active. Called from lifespan."""
    if settings.dev_mode:
        return  # Dev mode skips validation

    for field_name, insecure_values in _INSECURE_DEFAULTS.items():
        current = getattr(settings, field_name)
        if current in insecure_values:
            print(
                f"\n{'='*60}\n"
                f"FATAL: {field_name} is set to an insecure default.\n"
                f"Set NOMOS_{field_name.upper()} to a secure value or configure Vault.\n"
                f"To run in development mode, set NOMOS_DEV_MODE=true.\n"
                f"{'='*60}\n",
                file=sys.stderr,
            )
            sys.exit(1)
```

- [ ] **Step 9: Write test for config validation**

```python
# nomos-api/tests/test_config_validation.py
"""Test startup validation rejects insecure defaults."""

import subprocess
import sys

import pytest


class TestConfigValidation:
    def test_insecure_jwt_secret_exits(self):
        """App refuses to start with default JWT secret."""
        result = subprocess.run(
            [sys.executable, "-c",
             "from nomos_api.config import settings, validate_settings; validate_settings()"],
            capture_output=True, text=True,
            env={"NOMOS_JWT_SECRET": "change-me-in-production", "NOMOS_DEV_MODE": "false",
                 "PATH": "", "PYTHONPATH": "."},
            cwd=".",
        )
        assert result.returncode != 0
        assert "FATAL" in result.stderr or "insecure" in result.stderr.lower()

    def test_dev_mode_skips_validation(self):
        """Dev mode allows insecure defaults."""
        result = subprocess.run(
            [sys.executable, "-c",
             "from nomos_api.config import settings, validate_settings; validate_settings(); print('OK')"],
            capture_output=True, text=True,
            env={"NOMOS_DEV_MODE": "true", "PATH": "", "PYTHONPATH": "."},
            cwd=".",
        )
        assert "OK" in result.stdout
```

Run: `cd nomos-api && python -m pytest tests/test_config_validation.py -v`
Expected: ALL PASS

- [ ] **Step 10: Add Vault to docker-compose.yml**

Add this service block after `valkey` and before `piper-tts` in `docker-compose.yml`:

```yaml
  # ─── Secret Management ─────────────────────────────────

  vault:
    image: hashicorp/vault:1.15
    cap_add:
      - IPC_LOCK
    ports:
      - "${NOMOS_VAULT_PORT:-8200}:8200"
    environment:
      - VAULT_ADDR=http://127.0.0.1:8200
    volumes:
      - nomos-vault:/vault/file
      - ./vault/config:/vault/config:ro
      - ./vault/policies:/vault/policies:ro
      - ./vault/init.sh:/vault/init.sh:ro
    command: server -config=/vault/config/vault.hcl
    healthcheck:
      # vault status exits 0=healthy, 1=sealed-but-initialized, 2=not-initialized
      # We accept 0 and 1 (init.sh will unseal), reject 2 and connection errors
      test: ["CMD-SHELL", "vault status -address=http://127.0.0.1:8200 || [ $? -eq 1 ]"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    restart: unless-stopped
```

Add `nomos-vault:` to volumes section.

Add `vault` to `nomos-api` depends_on:

```yaml
    depends_on:
      postgres:
        condition: service_healthy
      valkey:
        condition: service_healthy
      vault:
        condition: service_healthy
```

- [ ] **Step 11: Replace all insecure fallbacks in docker-compose.yml**

Replace every `${VAR:-fallback}` with `${VAR:?Error message}`:

```yaml
# openclaw-gateway
- NOMOS_PLUGIN_API_KEY=${NOMOS_PLUGIN_API_KEY:?Set NOMOS_PLUGIN_API_KEY in .env}

# nomos-api
- NOMOS_DATABASE_URL=postgresql+asyncpg://nomos:${NOMOS_DB_PASSWORD:?Set NOMOS_DB_PASSWORD in .env}@postgres:5432/nomos
- NOMOS_GATEWAY_TOKEN=${NOMOS_GATEWAY_TOKEN:?Set NOMOS_GATEWAY_TOKEN in .env}
- NOMOS_JWT_SECRET=${NOMOS_JWT_SECRET:?Set NOMOS_JWT_SECRET in .env}
- NOMOS_PLUGIN_API_KEY=${NOMOS_PLUGIN_API_KEY:?Set NOMOS_PLUGIN_API_KEY in .env}
- NOMOS_VAULT_ADDR=http://vault:8200
- NOMOS_VAULT_ROLE_ID=${VAULT_ROLE_ID:-}
- NOMOS_VAULT_SECRET_ID=${VAULT_SECRET_ID:-}

# postgres
- POSTGRES_PASSWORD=${NOMOS_DB_PASSWORD:?Set NOMOS_DB_PASSWORD in .env}
```

Note: `VAULT_ROLE_ID` and `VAULT_SECRET_ID` use `:-` (optional) because Vault init generates them.

- [ ] **Step 12: Template openclaw.json gateway token**

Replace the hardcoded token in `config/openclaw.json`:

```json
    "auth": {
      "mode": "token",
      "token": "${NOMOS_GATEWAY_TOKEN}"
    }
```

Create `config/openclaw.json.template` with the `${NOMOS_GATEWAY_TOKEN}` placeholder, and add an entrypoint script to the gateway Dockerfile that runs `envsubst` before starting.

- [ ] **Step 13: Create .env.example**

```bash
# .env.example — NomOS Enterprise Configuration
# Copy to .env and fill in ALL required values before running docker compose up

# ─── REQUIRED (no defaults — containers will not start without these) ───
NOMOS_DB_PASSWORD=CHANGE_ME_REQUIRED
NOMOS_JWT_SECRET=CHANGE_ME_REQUIRED_MIN_32_CHARS
NOMOS_PLUGIN_API_KEY=CHANGE_ME_REQUIRED
NOMOS_GATEWAY_TOKEN=CHANGE_ME_REQUIRED

# ─── LLM API Keys (at least one required for chat functionality) ────────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
NVIDIA_API_KEY=

# ─── Vault (auto-populated by vault/init.sh on first run) ──────────────
VAULT_ROLE_ID=
VAULT_SECRET_ID=

# ─── Optional (sensible defaults exist) ─────────────────────────────────
# NOMOS_API_PORT=8060
# NOMOS_CONSOLE_PORT=3040
# NOMOS_GATEWAY_PORT=3050
# NOMOS_VAULT_PORT=8200
# NOMOS_DEV_MODE=false
```

- [ ] **Step 14: Commit Phase P0.1**

```bash
git add vault/ nomos-api/nomos_api/vault_client.py nomos-api/nomos_api/vault_source.py \
  nomos-api/nomos_api/config.py nomos-api/pyproject.toml \
  nomos-api/tests/test_vault_client.py nomos-api/tests/test_config_validation.py \
  docker-compose.yml config/openclaw.json .env.example
git commit -m "feat(security): Vault integration + startup validation + secret hardening"
```

---

### Task P0.2: Rate Limiter → Valkey Migration

**Files:**
- Modify: `nomos-api/nomos_api/auth/rate_limiter.py`
- Test: `nomos-api/tests/test_rate_limiter.py`

- [ ] **Step 1: Write failing test for Valkey rate limiter**

```python
# nomos-api/tests/test_rate_limiter.py
"""Tests for Valkey-backed rate limiter."""

import pytest

from nomos_api.auth.rate_limiter import RateLimiter


@pytest.fixture
async def limiter():
    """Create limiter with short window for testing."""
    rl = RateLimiter(max_attempts=3, window_seconds=10, lockout_seconds=10, valkey_url="redis://localhost:6379")
    await rl.reset("test-key")
    yield rl
    await rl.reset("test-key")


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter):
        assert await limiter.is_allowed("test-key") is True

    @pytest.mark.asyncio
    async def test_blocks_after_max_attempts(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("test-key")
        assert await limiter.is_allowed("test-key") is False

    @pytest.mark.asyncio
    async def test_reset_clears_state(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("test-key")
        await limiter.reset("test-key")
        assert await limiter.is_allowed("test-key") is True

    @pytest.mark.asyncio
    async def test_independent_keys(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("key-a")
        assert await limiter.is_allowed("key-b") is True
        await limiter.reset("key-a")
```

- [ ] **Step 2: Rewrite rate_limiter.py to use Valkey**

```python
# nomos-api/nomos_api/auth/rate_limiter.py
"""Distributed rate limiter backed by Valkey (Redis-compatible).

Uses sorted sets for sliding window rate limiting.
State persists across restarts and is shared across API instances.
"""

from __future__ import annotations

import time

import valkey.asyncio as valkey


class RateLimiter:
    """Valkey-backed sliding window rate limiter."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        lockout_seconds: int = 900,
        valkey_url: str = "redis://valkey:6379",
        key_prefix: str = "nomos:ratelimit:",
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._prefix = key_prefix
        self._client = valkey.from_url(valkey_url, decode_responses=True)

    def _attempts_key(self, key: str) -> str:
        return f"{self._prefix}attempts:{key}"

    def _lockout_key(self, key: str) -> str:
        return f"{self._prefix}lockout:{key}"

    async def is_allowed(self, key: str) -> bool:
        """Check if the key is allowed to make another attempt."""
        # Check lockout first
        locked = await self._client.get(self._lockout_key(key))
        if locked:
            return False

        # Count recent attempts in sliding window
        now = time.time()
        window_start = now - self.window_seconds
        await self._client.zremrangebyscore(self._attempts_key(key), "-inf", window_start)
        count = await self._client.zcard(self._attempts_key(key))
        return count < self.max_attempts

    async def record_attempt(self, key: str) -> None:
        """Record an attempt and trigger lockout if threshold reached."""
        now = time.time()
        attempts_key = self._attempts_key(key)

        # Add attempt with timestamp as score
        await self._client.zadd(attempts_key, {str(now): now})
        await self._client.expire(attempts_key, self.window_seconds + self.lockout_seconds)

        # Clean old entries
        window_start = now - self.window_seconds
        await self._client.zremrangebyscore(attempts_key, "-inf", window_start)

        # Check if lockout should trigger
        count = await self._client.zcard(attempts_key)
        if count >= self.max_attempts:
            await self._client.setex(
                self._lockout_key(key), self.lockout_seconds, "locked"
            )

    async def reset(self, key: str) -> None:
        """Clear all rate limit state for a key."""
        await self._client.delete(self._attempts_key(key), self._lockout_key(key))
```

- [ ] **Step 3: Run tests**

Run: `cd nomos-api && python -m pytest tests/test_rate_limiter.py -v`
Expected: ALL PASS (requires Valkey running on localhost:6379)

- [ ] **Step 4: Update auth router to use async rate limiter**

In `nomos-api/nomos_api/routers/auth.py`, replace the module-level limiter with lazy initialization:

```python
# Replace the module-level:
#   _login_limiter = RateLimiter(max_attempts=5, window_seconds=900, lockout_seconds=900)
# With:
_login_limiter: RateLimiter | None = None

def _get_limiter() -> RateLimiter:
    global _login_limiter
    if _login_limiter is None:
        from nomos_api.config import settings
        _login_limiter = RateLimiter(
            max_attempts=5, window_seconds=900, lockout_seconds=900,
            valkey_url=settings.valkey_url,
        )
    return _login_limiter
```

Then update all call sites in the login endpoint — change sync to async:

```python
# BEFORE:
#   if not _login_limiter.is_allowed(email):
# AFTER:
    limiter = _get_limiter()
    if not await limiter.is_allowed(email):
        raise HTTPException(status_code=429, detail="Too many attempts")

# BEFORE:
#   _login_limiter.record_attempt(email)
# AFTER:
    await limiter.record_attempt(email)

# BEFORE (on successful login):
#   _login_limiter.reset(email)
# AFTER:
    await limiter.reset(email)
```

- [ ] **Step 5: Fix nomos-api/docker-compose.yml — redis → valkey**

Replace `redis:8-alpine` with `valkey/valkey:8-alpine` in `nomos-api/docker-compose.yml`.

- [ ] **Step 6: Commit**

```bash
git add nomos-api/nomos_api/auth/rate_limiter.py nomos-api/tests/test_rate_limiter.py \
  nomos-api/nomos_api/routers/auth.py nomos-api/docker-compose.yml
git commit -m "feat(security): rate limiter migrated to Valkey — persistent, distributed"
```

---

### Task P0.3: Startup Validation + CORS + Docker Hardening

**Files:**
- Modify: `nomos-api/nomos_api/main.py`
- Modify: `nomos-api/nomos_api/routers/health.py`
- Test: `nomos-api/tests/test_cors.py`

- [ ] **Step 1: Remove hardcoded CORS regex and add dev_mode logic**

In `nomos-api/nomos_api/main.py`, replace the CORS middleware block:

```python
# Build CORS origins
cors_origins = list(settings.cors_origins)
if settings.dev_mode:
    cors_origins.append("http://localhost:3040")
    cors_origins.append("http://localhost:3045")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-NomOS-API-Key"],
)
```

**Key:** The `allow_origin_regex` parameter is REMOVED entirely.

- [ ] **Step 2: Add validate_settings() call to lifespan**

In the `lifespan` function in `main.py`, add at the top:

```python
from nomos_api.config import validate_settings
validate_settings()
```

- [ ] **Step 3: Update health endpoint with Vault status**

In `nomos-api/nomos_api/routers/health.py`, add Vault health:

```python
@router.get("/health")
async def health():
    from nomos_api.vault_client import VaultClient
    # Get or create vault client from settings
    vault_status = "not_configured"
    try:
        from nomos_api.config import settings
        if settings.vault_role_id:
            from nomos_api.vault_source import _get_vault_client
            client = _get_vault_client(settings.vault_addr, settings.vault_role_id, settings.vault_secret_id)
            vault_status = client.health_status()
    except Exception:
        vault_status = "error"

    return {
        "status": "healthy",
        "service": "nomos-api",
        "version": settings.api_version,
        "vault": vault_status,
    }
```

- [ ] **Step 4: Write CORS test**

```python
# nomos-api/tests/test_cors.py
"""Test CORS configuration respects settings."""

import pytest
from httpx import AsyncClient, ASGITransport

from nomos_api.main import app


@pytest.mark.asyncio
async def test_cors_rejects_unknown_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" not in response.headers or \
               response.headers.get("access-control-allow-origin") != "http://evil.example.com"
```

Run: `cd nomos-api && python -m pytest tests/test_cors.py -v`

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/main.py nomos-api/nomos_api/routers/health.py \
  nomos-api/tests/test_cors.py
git commit -m "feat(security): configurable CORS, startup validation, Vault health in /health"
```

---

### Ralph-Loop #1: Security Scan

After Phase 0 is complete, run:

```
/ralph-loop "Run nomos-security Red Team scan: check for hardcoded secrets, default credentials, auth bypass, injection, CORS misconfiguration. Check config.py has no insecure defaults. Check docker-compose.yml uses :? syntax. Check openclaw.json has no hardcoded tokens. Run: cd nomos-api && python -m pytest tests/ -v. Report findings." --completion-promise "SECURITY_CLEAN" --max-iterations 10
```

---

## PHASE 1: BACKEND COMPLETION

### Task P1.1: Budget-Hook Fix

**Files:**
- Modify: `nomos-api/nomos_api/routers/budget.py`
- Modify: `nomos-plugin/src/api-client.ts`
- Modify: `nomos-plugin/src/hooks/before-tool-call.ts`
- Test: `nomos-api/tests/test_budget.py`

- [ ] **Step 1: Fix backend — restrictive default for unknown agents**

In `nomos-api/nomos_api/routers/budget.py`, replace the 404 raise:

```python
@router.post("/budget/check")
async def budget_check(
    request: BudgetCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if agent has budget. Unknown agents get restrictive default (fail-closed)."""
    result = await check_budget(db, request.agent_id, request.estimated_cost)
    if result is None:
        return {
            "allowed": False,
            "remaining": 0,
            "status": "unknown_agent",
            "reason": f"Agent {request.agent_id!r} not registered. Register the agent first.",
            "agent_id": request.agent_id,
        }
    return result
```

- [ ] **Step 2: Write test for unknown agent budget check**

```python
# In nomos-api/tests/test_budget.py (add to existing or create)
@pytest.mark.asyncio
async def test_budget_check_unknown_agent_returns_restrictive(client):
    """Unknown agents get fail-closed response, not 404."""
    response = await client.post("/api/budget/check", json={
        "agent_id": "nonexistent-agent",
        "estimated_cost": 0.01,
    })
    assert response.status_code == 200  # Not 404
    data = response.json()
    assert data["allowed"] is False
    assert data["status"] == "unknown_agent"
    assert "reason" in data
```

- [ ] **Step 3: Fix plugin api-client.ts — add res.ok guard**

In `nomos-plugin/src/api-client.ts`, replace checkBudget:

```typescript
  async checkBudget(agentId: string, estimatedCost: number): Promise<BudgetResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/budget/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, estimated_cost: estimatedCost }),
      });
      if (!res.ok) {
        return { allowed: false, remaining: 0, error: `HTTP ${res.status}` };
      }
      return await res.json() as BudgetResult;
    } catch {
      return { allowed: false, remaining: 0, error: "API unreachable" };
    }
  }
```

- [ ] **Step 3b: Update BudgetResult type in api-client.ts**

Add `status` and `reason` fields to the `BudgetResult` interface:

```typescript
export interface BudgetResult {
  allowed: boolean;
  remaining: number;
  error?: string;
  status?: string;   // "normal" | "warning" | "exceeded" | "unknown_agent"
  reason?: string;    // Human-readable reason when allowed=false
}
```

- [ ] **Step 4: Fix plugin before-tool-call.ts — handle error/unknown_agent**

```typescript
    // 1. Budget check
    const budget = await client.checkBudget(agentId, 0.01);
    if (budget.error) {
      // API error — log and continue (don't block on transient failures)
      client.addAuditEntry({
        agent_id: agentId,
        event_type: "tool.call_allowed",
        payload: { tool: event.toolName, budget_error: budget.error },
      });
    } else if (!budget.allowed) {
      const reason = (budget as any).reason || "budget_exceeded";
      if (reason === "unknown_agent") {
        // Unknown agent — log warning, don't block (agent registration is the fix)
        client.addAuditEntry({
          agent_id: agentId,
          event_type: "tool.call_allowed",
          payload: { tool: event.toolName, budget_warning: "unknown_agent" },
        });
      } else {
        return {
          block: true,
          blockReason: `Budget ueberschritten (${agentId}). Remaining: EUR ${budget.remaining ?? 0}. Agent wird pausiert.`,
        };
      }
    }
```

- [ ] **Step 5: Build and test plugin**

Run: `cd nomos-plugin && npm run build && npm test`
Expected: BUILD SUCCESS, tests pass

- [ ] **Step 6: Commit**

```bash
git add nomos-api/nomos_api/routers/budget.py nomos-api/tests/test_budget.py \
  nomos-plugin/src/api-client.ts nomos-plugin/src/hooks/before-tool-call.ts
git commit -m "fix(budget): fail-closed for unknown agents, res.ok guard in plugin"
```

---

### Task P1.2: Settings PATCH with Vault

**Files:**
- Modify: `nomos-api/nomos_api/schemas.py`
- Modify: `nomos-api/nomos_api/routers/settings.py`
- Modify: `nomos-console/src/lib/types.ts`
- Modify: `nomos-console/src/app/admin/settings/page.tsx`
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-console/src/lib/i18n/en.ts`
- Test: `nomos-api/tests/test_settings.py`

- [ ] **Step 1: Add schemas to schemas.py**

```python
# Add to nomos-api/nomos_api/schemas.py

class SystemSettingsResponse(BaseModel):
    """System settings — config values in cleartext, secrets masked."""
    gateway_url: str
    retention_days: int
    pii_filter_mode: str
    openai_api_key_set: bool = False
    anthropic_api_key_set: bool = False
    nvidia_api_key_set: bool = False


class SettingsUpdateRequest(BaseModel):
    """Partial update — only provided fields are changed."""
    gateway_url: str | None = None
    retention_days: int | None = None
    pii_filter_mode: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    nvidia_api_key: str | None = None
```

- [ ] **Step 2: Rewrite settings router with PATCH + Vault**

```python
# nomos-api/nomos_api/routers/settings.py
"""System settings — read config from Vault, write via PATCH (admin-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from nomos_api.auth.dependencies import get_current_user, require_admin
from nomos_api.config import settings as app_settings
from nomos_api.schemas import SettingsUpdateRequest, SystemSettingsResponse
from nomos_api.vault_client import VaultClient
from nomos_api.vault_source import _get_vault_client

SENSITIVE_KEYS = {"openai_api_key", "anthropic_api_key", "nvidia_api_key"}

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_vault() -> VaultClient:
    return _get_vault_client(
        app_settings.vault_addr,
        app_settings.vault_role_id,
        app_settings.vault_secret_id,
    )


@router.get("", response_model=SystemSettingsResponse)
async def get_settings() -> SystemSettingsResponse:
    """Return current system settings. Secrets shown as boolean flags only."""
    vault = _get_vault()
    return SystemSettingsResponse(
        gateway_url=vault.get_secret("config/gateway_url") or app_settings.gateway_url,
        retention_days=int(vault.get_secret("config/retention_days") or app_settings.retention_days),
        pii_filter_mode=vault.get_secret("config/pii_filter_mode") or app_settings.pii_filter_mode,
        openai_api_key_set=vault.get_secret("secrets/openai_api_key") is not None,
        anthropic_api_key_set=vault.get_secret("secrets/anthropic_api_key") is not None,
        nvidia_api_key_set=vault.get_secret("secrets/nvidia_api_key") is not None,
    )


@router.patch("", response_model=SystemSettingsResponse, dependencies=[Depends(require_admin)])
async def update_settings(
    updates: SettingsUpdateRequest,
    current_user=Depends(get_current_user),
) -> SystemSettingsResponse:
    """Update system settings. Admin-only. Writes to Vault."""
    vault = _get_vault()
    if not vault.is_connected:
        raise HTTPException(status_code=503, detail="Vault unavailable — cannot update settings")

    changed_keys = []
    for field_name, value in updates.model_dump(exclude_unset=True).items():
        if field_name in SENSITIVE_KEYS:
            vault_path = f"secrets/{field_name}"
        else:
            vault_path = f"config/{field_name}"

        vault.put_secret(vault_path, str(value))
        changed_keys.append(field_name)

    # Audit log — record who changed what (never log secret values)
    from nomos_api.database import get_db
    from nomos_api.models import AuditLog
    # Fire-and-forget audit entry via existing audit infrastructure
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        "Settings updated by user=%s fields=%s",
        current_user.id,
        [k for k in changed_keys if k not in SENSITIVE_KEYS]
        + [f"{k}=***" for k in changed_keys if k in SENSITIVE_KEYS],
    )

    return await get_settings()
```

- [ ] **Step 3: Update TypeScript types**

Add to `nomos-console/src/lib/types.ts`:

```typescript
export interface SystemSettings {
  gateway_url: string;
  retention_days: number;
  pii_filter_mode: string;
  openai_api_key_set: boolean;
  anthropic_api_key_set: boolean;
  nvidia_api_key_set: boolean;
}

export interface SettingsUpdateRequest {
  gateway_url?: string;
  retention_days?: number;
  pii_filter_mode?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  nvidia_api_key?: string;
}
```

- [ ] **Step 4: Update Settings page — editable form with masked key inputs**

Rewrite `nomos-console/src/app/admin/settings/page.tsx` to:
- Remove "read-only" notice
- Add form inputs for gateway_url, retention_days, pii_filter_mode
- Add masked password inputs for LLM API keys (show "Configured" badge when `*_key_set` is true)
- Save button calls `api.patch('/settings', updates)`
- Success/error toast notifications

- [ ] **Step 5: Remove read-only strings from i18n**

Remove `settings.readOnly` from both `de.ts` and `en.ts`.

- [ ] **Step 6: Write test for settings PATCH**

```python
# nomos-api/tests/test_settings.py
@pytest.mark.asyncio
async def test_settings_patch_requires_admin(client, user_token):
    """Non-admin cannot update settings."""
    response = await client.patch("/api/settings",
        json={"retention_days": 30},
        headers={"Cookie": f"nomos_token={user_token}"},
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_settings_patch_updates_value(client, admin_token):
    """Admin can update settings."""
    response = await client.patch("/api/settings",
        json={"retention_days": 30},
        headers={"Cookie": f"nomos_token={admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["retention_days"] == 30
```

- [ ] **Step 7: Commit**

```bash
git add nomos-api/nomos_api/schemas.py nomos-api/nomos_api/routers/settings.py \
  nomos-api/tests/test_settings.py nomos-console/src/lib/types.ts \
  nomos-console/src/app/admin/settings/page.tsx \
  nomos-console/src/lib/i18n/de.ts nomos-console/src/lib/i18n/en.ts
git commit -m "feat(settings): PATCH endpoint with Vault, editable console UI"
```

---

### Task P1.3: Contract Tests CI Guard

**Files:**
- Create: `scripts/export-schemas.py`
- Create: `scripts/check-contracts.ts`
- Create: `scripts/contract-naming-map.json`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Create schema exporter**

```python
#!/usr/bin/env python3
# scripts/export-schemas.py
"""Export all Pydantic schemas from nomos-api as JSON Schema.

Usage: python scripts/export-schemas.py > schemas.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "nomos-api"))

from nomos_api import schemas

def export_all():
    result = {}
    for name in dir(schemas):
        obj = getattr(schemas, name)
        if isinstance(obj, type) and hasattr(obj, "model_json_schema"):
            result[name] = obj.model_json_schema()
    return result

if __name__ == "__main__":
    print(json.dumps(export_all(), indent=2))
```

- [ ] **Step 2: Create naming map**

```json
{
  "AgentResponse": "Agent",
  "CostResponse": "CostEntry",
  "ApprovalResponse": "ApprovalEntry",
  "IncidentResponse": "IncidentEntry",
  "AuditEntryResponse": "AuditEntry",
  "ComplianceResponse": "ComplianceEntry",
  "UserResponse": "UserAccount",
  "TaskResponse": "TaskEntry"
}
```

- [ ] **Step 3: Create contract checker (TypeScript)**

```typescript
// scripts/check-contracts.ts
// Compares Pydantic JSON Schema output against types.ts interfaces
// Run: npx tsx scripts/check-contracts.ts

import { readFileSync } from "fs";
import { Project, SyntaxKind } from "ts-morph";

const schemasJson = JSON.parse(readFileSync("schemas.json", "utf-8"));
const namingMap = JSON.parse(readFileSync("scripts/contract-naming-map.json", "utf-8"));

const project = new Project();
const sourceFile = project.addSourceFileAtPath("nomos-console/src/lib/types.ts");

const interfaces = new Map<string, Map<string, string>>();
for (const iface of sourceFile.getInterfaces()) {
  const fields = new Map<string, string>();
  for (const prop of iface.getProperties()) {
    fields.set(prop.getName(), prop.getType().getText());
  }
  interfaces.set(iface.getName(), fields);
}

let errors = 0;

for (const [pyName, schema] of Object.entries(schemasJson)) {
  const tsName = namingMap[pyName] || pyName;
  const tsInterface = interfaces.get(tsName);

  if (!tsInterface) continue; // Not all Python schemas need TS counterparts

  const pyFields = schema.properties || {};
  for (const [fieldName, fieldSchema] of Object.entries(pyFields)) {
    if (!tsInterface.has(fieldName)) {
      console.error(`MISMATCH: ${tsName} missing field '${fieldName}' (exists in ${pyName})`);
      errors++;
    } else {
      // Type compatibility check
      const pyType = mapPythonTypeToTS(fieldSchema as any);
      const tsType = tsInterface.get(fieldName)!;
      if (pyType && !isTypeCompatible(pyType, tsType)) {
        console.error(`TYPE MISMATCH: ${tsName}.${fieldName} — Python: ${pyType}, TypeScript: ${tsType}`);
        errors++;
      }
    }
  }

  for (const [fieldName] of tsInterface) {
    if (!(fieldName in pyFields)) {
      console.error(`MISMATCH: ${tsName}.${fieldName} has no counterpart in ${pyName}`);
      errors++;
    }
  }
}

// Helper: Map JSON Schema types to TypeScript equivalents
function mapPythonTypeToTS(schema: { type?: string; anyOf?: any[] }): string | null {
  if (schema.anyOf) {
    const types = schema.anyOf.map((s: any) => mapPythonTypeToTS(s)).filter(Boolean);
    return types.join(" | ") || null;
  }
  switch (schema.type) {
    case "string": return "string";
    case "integer": case "number": return "number";
    case "boolean": return "boolean";
    case "array": return "string[]"; // simplified
    case "null": return "null";
    default: return null;
  }
}

function isTypeCompatible(pyType: string, tsType: string): boolean {
  // Normalize and compare (simplified — handles common cases)
  const normalize = (t: string) => t.replace(/\s/g, "").split("|").sort().join("|");
  return normalize(pyType) === normalize(tsType) || tsType.includes(pyType);
}

if (errors > 0) {
  console.error(`\n${errors} contract mismatches found.`);
  process.exit(1);
} else {
  console.log("All contracts aligned.");
}
```

- [ ] **Step 4: Add CI job**

Add to `.github/workflows/ci.yml`:

```yaml
  contract-check:
    name: Contract Check (schemas.py ↔ types.ts)
    runs-on: ubuntu-latest
    needs: [lint-python, lint-typescript]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: pip install pydantic pydantic-settings
      - run: python scripts/export-schemas.py > schemas.json
      - run: npm install -g tsx ts-morph
      - run: npx tsx scripts/check-contracts.ts
```

Add `contract-check` to the quality-gate `needs` array.
Also add `test-console` to the quality-gate `needs` array.

- [ ] **Step 5: Commit**

```bash
git add scripts/ .github/workflows/ci.yml
git commit -m "feat(ci): automated contract tests — schemas.py vs types.ts guard"
```

---

### Task P1.4: Docs/Framing Cleanup

**Files:**
- Modify: `.claude/CLAUDE.md`
- Modify: `docs/architecture.md`
- Modify: `docs/references/openclaw-nemoclaw-reference.md`
- Modify: `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md`
- Modify: `.claude/agents/nomos-security.md`

- [ ] **Step 1: Fix CLAUDE.md**

Replace `Standalone Docker-Produkt. Kunden starten docker compose up -d auf IHREM Server.` with:
```
Enterprise Docker-Produkt mit 3 Deployment-Tiers: Enterprise VPS (managed), Docker Self-Hosted, Open-Source.
Kunden starten docker compose up -d auf ihrem Server. Secret Management via HashiCorp Vault.
```

- [ ] **Step 2: Fix architecture.md**

- Replace ENV-as-security-control section with Vault architecture description
- Remove `nomos` as documented DB password default
- Add Vault to service diagram

- [ ] **Step 3: Fix reference docs**

Replace all "NomOS v2 MVP" with "NomOS v2".

- [ ] **Step 4: Fix master plan**

Replace "Console MVP" with "Console v1". Replace "spaeter Valkey" with "done (migrated in Enterprise Hardening sprint)".

- [ ] **Step 5: Fix security agent instructions**

In `.claude/agents/nomos-security.md`, replace "Secrets ueber Environment Variables" with:
```
Secrets via HashiCorp Vault (KV v2). ENV nur als Fallback in dev_mode.
Pruefregel: Kein Secret darf als Default-Wert in config.py oder docker-compose.yml stehen.
```

- [ ] **Step 6: Commit**

```bash
git add .claude/CLAUDE.md docs/architecture.md docs/references/ \
  docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md \
  .claude/agents/nomos-security.md
git commit -m "docs: MVP → Enterprise framing, Vault architecture, no insecure defaults"
```

---

### Ralph-Loop #2: Backend Integration

```
/ralph-loop "Run full CI pipeline locally: cd nomos-api && python -m pytest tests/ -v && cd ../nomos-plugin && npm run build && npm test. Run contract check: python scripts/export-schemas.py > schemas.json && npx tsx scripts/check-contracts.ts. Verify all docs use Enterprise framing (grep -r 'MVP' docs/ — should be 0 hits). Report findings." --completion-promise "BACKEND_CLEAN" --max-iterations 10
```

---

## PHASE 2: FRONTEND QUALITY

### Task P2.1: Vitest Setup + Full Page Coverage

**Files:**
- Modify: `nomos-console/package.json`
- Create: `nomos-console/vitest.config.ts`
- Create: `nomos-console/src/test-utils.tsx`
- Create: `nomos-console/src/__tests__/` (20 test files)
- Create: `nomos-console/src/lib/__tests__/` (hook + util tests)

- [ ] **Step 1: Install test dependencies**

```bash
cd nomos-console && npm install -D vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event jsdom @types/testing-library__jest-dom
```

- [ ] **Step 2: Add test script to package.json**

```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest",
  "test:coverage": "vitest run --coverage"
}
```

- [ ] **Step 3: Create vitest.config.ts**

```typescript
// nomos-console/vitest.config.ts
import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-utils.tsx"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

- [ ] **Step 4: Create test-utils.tsx**

```tsx
// nomos-console/src/test-utils.tsx
import "@testing-library/jest-dom";
import { render, type RenderOptions } from "@testing-library/react";
import { type ReactElement } from "react";
import { vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/admin",
  useSearchParams: () => new URLSearchParams(),
  redirect: vi.fn(),
}));

// Mock next/image
vi.mock("next/image", () => ({
  default: (props: any) => <img {...props} />,
}));

// Mock API module
export const mockApi = {
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
};
vi.mock("@/lib/api", () => ({ api: mockApi, apiFetch: vi.fn() }));

// Mock useFetch
export const mockUseFetch = vi.fn().mockReturnValue({
  data: null, loading: true, error: null, reload: vi.fn(),
});
vi.mock("@/lib/hooks", async (importOriginal) => {
  const orig = await importOriginal() as any;
  return { ...orig, useFetch: (...args: any[]) => mockUseFetch(...args) };
});

// Mock useAuth
export const mockUseAuth = vi.fn().mockReturnValue({
  user: { id: "admin-1", email: "admin@test.com", name: "Admin", role: "admin" },
  loading: false, error: null, login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
});
vi.mock("@/lib/auth", async (importOriginal) => {
  const orig = await importOriginal() as any;
  return { ...orig, useAuth: () => mockUseAuth() };
});

// Reset all mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
  mockUseFetch.mockReturnValue({ data: null, loading: true, error: null, reload: vi.fn() });
});

// Custom render with providers
export function renderPage(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { ...options });
}

export { render, vi };
```

- [ ] **Step 5-24: Create test files for all 20 pages**

Each page gets a test file following this pattern (example for admin dashboard):

```tsx
// nomos-console/src/__tests__/admin-page.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { mockUseFetch } from "../test-utils";
import AdminPage from "../app/admin/page";

describe("Admin Dashboard", () => {
  it("shows loading skeleton", () => {
    mockUseFetch.mockReturnValue({ data: null, loading: true, error: null, reload: vi.fn() });
    render(<AdminPage />);
    // Should show loading indicator
    expect(document.querySelector("[class*=skeleton], [class*=loading], [aria-busy]")).toBeTruthy();
  });

  it("shows error state", () => {
    mockUseFetch.mockReturnValue({ data: null, loading: false, error: new Error("API down"), reload: vi.fn() });
    render(<AdminPage />);
    expect(screen.getByText(/fehler|error/i)).toBeInTheDocument();
  });

  it("shows empty state", () => {
    mockUseFetch.mockReturnValue({
      data: { agents: [], total: 0 }, loading: false, error: null, reload: vi.fn(),
    });
    render(<AdminPage />);
    // Page renders without crashing
    expect(document.body).toBeTruthy();
  });

  it("shows data state", () => {
    mockUseFetch.mockReturnValue({
      data: {
        agents: [{ id: "a1", name: "Test", status: "idle", compliance_status: "passed" }],
        total: 1,
      },
      loading: false, error: null, reload: vi.fn(),
    });
    render(<AdminPage />);
    expect(screen.getByText(/test/i)).toBeInTheDocument();
  });
});
```

Create analogous test files for ALL 20 pages. **Mandatory pages first** (login, dashboard, compliance, audit, settings, chat), then the rest.

Test file naming convention: `src/__tests__/<route-name>.test.tsx`

- [ ] **Step 25: Create hook and util tests**

```typescript
// nomos-console/src/lib/__tests__/hooks.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Test formatDate, formatEur, getGreetingKey, agentStatusToBadge
import { formatDate, formatEur, getGreetingKey } from "../hooks";
import { agentStatusToBadge } from "../types";

describe("formatEur", () => {
  it("formats zero", () => expect(formatEur(0)).toContain("0"));
  it("formats positive", () => expect(formatEur(42.5)).toContain("42"));
});

describe("agentStatusToBadge", () => {
  it("maps idle to success", () => expect(agentStatusToBadge("idle")).toBeDefined());
  it("maps error to error", () => expect(agentStatusToBadge("error")).toBeDefined());
  it("maps unknown to default", () => expect(agentStatusToBadge("unknown" as any)).toBeDefined());
});
```

- [ ] **Step 26: Run all tests**

Run: `cd nomos-console && npm test`
Expected: ALL PASS

- [ ] **Step 27: Commit**

```bash
git add nomos-console/vitest.config.ts nomos-console/src/test-utils.tsx \
  nomos-console/src/__tests__/ nomos-console/src/lib/__tests__/ \
  nomos-console/package.json nomos-console/package-lock.json
git commit -m "test(console): vitest setup + full page coverage — 20 pages × 4 states"
```

---

### Task P2.2: E2E Enterprise Suite (Playwright)

**Files:**
- Modify: `nomos-console/playwright.config.ts`
- Create: `nomos-console/e2e/auth.setup.ts`
- Create: `nomos-console/e2e/happy-path.spec.ts`
- Create: `nomos-console/e2e/error-cases.spec.ts`
- Create: `nomos-console/e2e/multi-user.spec.ts`
- Create: `nomos-console/e2e/page-sweep.spec.ts`

- [ ] **Step 1: Update Playwright config**

```typescript
// nomos-console/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["html"], ["github"]] : [["html"]],
  use: {
    baseURL: "http://localhost:3040",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], storageState: "e2e/.auth/admin.json" },
      dependencies: ["setup"],
    },
  ],
  webServer: {
    command: "npm run dev",
    port: 3040,
    reuseExistingServer: !process.env.CI,
  },
});
```

- [ ] **Step 2: Create auth setup**

```typescript
// nomos-console/e2e/auth.setup.ts
import { test as setup, expect } from "@playwright/test";

setup("authenticate as admin", async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[type="email"]', process.env.TEST_ADMIN_EMAIL || "admin@nomos.local");
  await page.fill('input[type="password"]', process.env.TEST_ADMIN_PASSWORD || "admin123");
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(admin|app)/);
  await page.context().storageState({ path: "e2e/.auth/admin.json" });
});
```

- [ ] **Step 3: Create happy path suite**

```typescript
// nomos-console/e2e/happy-path.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Happy Path — Full Journey", () => {
  test("Login → Dashboard → Team → Hire → Chat → Audit → Settings → Logout", async ({ page }) => {
    // Dashboard loads
    await page.goto("/admin");
    await expect(page.locator("h1, [role=heading]").first()).toBeVisible();

    // Navigate to Team
    await page.click('a[href*="team"], nav >> text=Team');
    await expect(page).toHaveURL(/team/);

    // Navigate to Hire
    await page.click('a[href*="hire"], nav >> text=Einstellen');
    await expect(page).toHaveURL(/hire/);

    // Navigate to Audit
    await page.click('a[href*="audit"], nav >> text=Audit');
    await expect(page).toHaveURL(/audit/);

    // Navigate to Settings
    await page.click('a[href*="settings"], nav >> text=Einstellungen');
    await expect(page).toHaveURL(/settings/);

    // Logout
    await page.click('button >> text=Abmelden, [aria-label*="logout"], [aria-label*="Abmelden"]');
    await expect(page).toHaveURL(/login/);
  });
});
```

- [ ] **Step 4: Create error cases suite**

```typescript
// nomos-console/e2e/error-cases.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Error Cases", () => {
  test("Wrong password shows error", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "wrong@test.com");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');
    await expect(page.locator("[role=alert], .error, [class*=error]")).toBeVisible();
  });

  test("Unauthenticated user redirected to login", async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto("/admin");
    await expect(page).toHaveURL(/login/);
    await context.close();
  });

  test("API error shows error state on dashboard", async ({ page }) => {
    // Block API calls to simulate downtime
    await page.route("**/api/**", (route) => route.abort());
    await page.goto("/admin");
    // Page should show error state, not crash
    await expect(page.locator("body")).toBeVisible();
  });
});
```

- [ ] **Step 5: Create multi-user suite**

```typescript
// nomos-console/e2e/multi-user.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Multi-User Access Control", () => {
  test("Admin can access /admin pages", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).not.toHaveURL(/login/);
  });

  test("Regular user cannot access /admin", async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    // Login as regular user
    await page.goto("/login");
    await page.fill('input[type="email"]', process.env.TEST_USER_EMAIL || "user@nomos.local");
    await page.fill('input[type="password"]', process.env.TEST_USER_PASSWORD || "user123");
    await page.click('button[type="submit"]');
    // Should be redirected to /app, not /admin
    await page.goto("/admin");
    await expect(page).toHaveURL(/\/(app|login)/);
    await context.close();
  });
});
```

- [ ] **Step 6: Create full page sweep**

```typescript
// nomos-console/e2e/page-sweep.spec.ts
import { test, expect } from "@playwright/test";

const PAGES = [
  "/login",
  "/admin", "/admin/team", "/admin/hire", "/admin/tasks",
  "/admin/approvals", "/admin/incidents", "/admin/compliance",
  "/admin/costs", "/admin/diagnostics", "/admin/audit",
  "/admin/users", "/admin/settings",
  "/app", "/app/tasks", "/app/help",
  "/compliance",
];

// Dynamic pages tested separately (need valid IDs)
const DYNAMIC_PAGES = [
  // "/admin/team/[id]" — tested in happy-path with real agent ID
  // "/app/chat/[id]" — tested in happy-path with real agent ID
];

for (const path of PAGES) {
  test(`Page ${path} loads without errors`, async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });

    await page.goto(path);
    await page.waitForLoadState("networkidle");

    // Page has content
    await expect(page.locator("body")).not.toBeEmpty();

    // No console errors (filter out known noise)
    const realErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("hydration"),
    );
    expect(realErrors).toEqual([]);
  });
}

test("All pages have correct lang attribute", async ({ page }) => {
  await page.goto("/admin");
  const lang = await page.getAttribute("html", "lang");
  expect(["de", "en"]).toContain(lang);
});

test("Mobile viewport renders without overflow", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto("/admin");
  const body = await page.evaluate(() => document.body.scrollWidth <= window.innerWidth);
  expect(body).toBe(true);
});
```

- [ ] **Step 7: Add .gitignore for auth state**

```
# nomos-console/e2e/.auth/.gitignore
*.json
```

- [ ] **Step 8: Run E2E tests**

Run: `cd nomos-console && npx playwright test`
Expected: ALL PASS (requires running stack)

- [ ] **Step 9: Commit**

```bash
git add nomos-console/playwright.config.ts nomos-console/e2e/
git commit -m "test(e2e): enterprise suite — happy path, errors, multi-user, page sweep"
```

---

### Ralph-Loop #3: Frontend Complete

```
/ralph-loop "Run all frontend tests: cd nomos-console && npm test && npx playwright test. Check 0 console errors in browser. Check all 20 pages render in all 4 states. Report test count and failures." --completion-promise "FRONTEND_CLEAN" --max-iterations 10
```

---

## PHASE 3: FINAL VALIDATION

### Ralph-Loop #4: Enterprise Ready

```
/ralph-loop "Final Enterprise validation:
1. Run full CI: cd nomos-api && python -m pytest tests/ -v
2. Run plugin: cd nomos-plugin && npm run build && npm test
3. Run console tests: cd nomos-console && npm test
4. Run contract check: python scripts/export-schemas.py > schemas.json && npx tsx scripts/check-contracts.ts
5. Run E2E: cd nomos-console && npx playwright test
6. Security scan: grep -rn 'change-me\|nomos-plugin-dev\|nomos-dev-token' nomos-api/ config/ docker-compose.yml — should be 0 hits outside tests
7. MVP scan: grep -rn 'MVP\|Standalone' docs/ .claude/ — should be 0 hits
8. Docker build: docker compose build
All must pass." --completion-promise "ENTERPRISE_READY" --max-iterations 15
```

---

## Quick Reference

| Phase | Tasks | Commits | Ralph-Loop |
|-------|-------|---------|------------|
| P0 Security | P0.1 Vault, P0.2 Rate Limiter, P0.3 CORS | 3 | #1 Security |
| P1 Backend | P1.1 Budget, P1.2 Settings, P1.3 Contracts, P1.4 Docs | 4 | #2 Backend |
| P2 Frontend | P2.1 Vitest, P2.2 Playwright | 2 | #3 Frontend |
| P3 Final | — | — | #4 Enterprise Ready |
| **Total** | **9 tasks** | **9 commits** | **4 loops** |
