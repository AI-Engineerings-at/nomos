# nomos-api

> FastAPI Control Plane for NomOS. Python 3.12, Pydantic v2, async
> SQLAlchemy + asyncpg + Alembic, ARQ worker on Valkey, Vault-first
> settings source.

Top-level overview: [`../README.md`](../README.md). End-to-end
architecture: [`../docs/architecture.md`](../docs/architecture.md).

## 1. Purpose & Boundary

The HTTP surface and background worker of NomOS. Owns Postgres
writes, exposes 19 routers under `/api/*`, runs 7 cron jobs in the
ARQ worker, and signs every audit-chain entry it writes. Does NOT
talk to an LLM directly — chat traffic is proxied through the
OpenClaw gateway via the plugin.

Imports `nomos.core.*` from `../nomos-cli/nomos/` (shared library:
`hash_chain`, `manifest`, `gate`, `compliance_engine`, `events`,
`forge`, `merkle`). Tests run with `PYTHONPATH="../nomos-cli"` to
match this import path.

## 2. Prerequisites

- Python 3.12 (CI runs 3.12 only).
- `uv` (or pip + venv).
- PostgreSQL 16 with `pgvector` (the `pgvector/pgvector:pg16` image
  is what the stack builds against — `docker-compose.yml`).
- Valkey 8 (BSD-3 Redis replacement) for rate limiting + ARQ.
- HashiCorp Vault 1.17 for secrets in production; ENV fallback in dev.

## 3. Dev Setup

```bash
cd nomos-api
uv sync --extra dev                       # install runtime + test deps
alembic upgrade head                      # apply migrations
uvicorn nomos_api.main:app --reload \
  --host 0.0.0.0 --port 8060              # local API
python -m arq nomos_api.worker.main.WorkerSettings  # local worker
```

Docs surfaces while running: Swagger UI `http://localhost:8060/docs`,
ReDoc `http://localhost:8060/redoc`.

## 4. Environment Variables

All secrets must come from Vault in production. The CI workflow
documents the exact CI-only test values
([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)). Key vars
specific to this package:

| Variable | Required | Purpose |
|---|---|---|
| `NOMOS_DATABASE_URL` | yes | `postgresql+asyncpg://...` |
| `NOMOS_VALKEY_URL` | yes | `valkey://valkey:6379` |
| `NOMOS_JWT_SECRET` | yes (≥32 chars) | Session-token signing |
| `NOMOS_PLUGIN_API_KEY` | yes (≥32 chars) | Plugin/service auth header |
| `NOMOS_GATEWAY_TOKEN` | yes | Gateway ↔ API bidirectional auth |
| `NOMOS_DB_PASSWORD` | yes | Postgres password (compose `:?` guarded) |
| `NOMOS_HASHCHAIN_HMAC_KEY` | yes (≥32 bytes) | Audit-chain HMAC anchor (fail-closed) |
| `NOMOS_AUDIT_SIGNING_KEY` | yes (32-byte hex seed) | Ed25519 audit signing (fail-closed) |
| `NOMOS_AGENTS_DIR` | yes | Filesystem root for agent dirs (`/data/agents` in compose) |
| `NOMOS_DEV_MODE` | no (default `false`) | Enables dev fallbacks; never true in prod |
| `NOMOS_COOKIE_SECURE` | no (default `true`) | HSTS + Secure-cookie toggle |
| `NOMOS_DOMAIN` | no (default `localhost`) | Public domain for Caddy TLS |

Full table including ARQ + monitoring vars: [`../docs/architecture.md`](../docs/architecture.md) "Configuration".

## 5. Tests

```bash
# Inside nomos-api/, dev extras installed:
PYTHONPATH="../nomos-cli" uv run python -m pytest -v
# Subset:
PYTHONPATH="../nomos-cli" uv run python -m pytest tests/test_audit_merkle_phase_b1.py -v
```

454 tests as of 0.2.0 (chunked 170 + 119 + 165 — same chunking is
recommended locally on Windows to avoid SQLite-in-memory state
leakage between heavy router suites).

CI runs migrations on a real Postgres service container BEFORE the
suite — `Base.metadata.create_all` on SQLite cannot catch
model↔migration drift, so the live Alembic run is the canonical
schema gate (`.github/workflows/ci.yml` "Apply Alembic migrations").

## 6. Build & Ship

```bash
docker compose build nomos-api nomos-worker
docker compose up -d nomos-api nomos-worker
docker compose logs -f nomos-api | grep -i alembic   # confirm migrations
```

Version bump: `pyproject.toml` `version`. Bump together with
`nomos-cli` (shared `nomos.core`) and `nomos-console`. Update
`CHANGELOG.md` entry.

Healthcheck: container runs `curl localhost:8000/health` internally.
External: `curl http://localhost:8060/health` returns
`{status: healthy|degraded, components: {vault, postgres, valkey, gateway}}`.

## 7. Common Gotchas

- **Alembic head mismatch on dev DB** — drop the local
  `nomos_dev` DB and re-`upgrade head`, or run on the compose
  Postgres which is always migrated by the API container at boot.
- **`HashChainKeyMissing` / `AuditSignatureKeyMissing` on startup** —
  fail-closed by design; set both `NOMOS_HASHCHAIN_HMAC_KEY` and
  `NOMOS_AUDIT_SIGNING_KEY` (32-byte hex seeds). In CI these are
  inline ENV; in prod they must come from Vault.
- **PYTHONPATH for tests** — `nomos.core` lives in `../nomos-cli`.
  Both local and CI invocations need `PYTHONPATH="../nomos-cli"`.
- **Vault token expiry** — long-running dev sessions may hit token
  expiry; restart `nomos-api` to re-fetch a fresh lease.
- **Async session in pytest-asyncio** — use `async_sessionmaker`
  (not `sessionmaker`) and remember `expire_on_commit=False` for
  tests that read after commit.
