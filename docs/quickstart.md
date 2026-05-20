# NomOS Quickstart Guide

Get NomOS running in 5 minutes.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose v2 (Linux)
- Minimum 4 GB RAM allocated to Docker
- Ports 80 and 443 available (or configure custom ports in `.env`)

## 1. Clone and Configure

```bash
git clone https://github.com/ai-engineering-at/nomos.git
cd nomos
cp .env.example .env
```

Open `.env` in your editor and set the four **required** secrets — Docker will refuse to start with the placeholder values:

| Variable | Description | Example |
|---|---|---|
| `NOMOS_JWT_SECRET` | 32+ character secret for session tokens | `openssl rand -hex 32` |
| `NOMOS_PLUGIN_API_KEY` | Auth key for OpenClaw gateway communication | `openssl rand -hex 24` |
| `NOMOS_GATEWAY_TOKEN` | Bidirectional gateway ↔ API auth token | `openssl rand -hex 24` |
| `NOMOS_DB_PASSWORD` | PostgreSQL password | any strong password |

Generate all four at once:

```bash
echo "NOMOS_JWT_SECRET=$(openssl rand -hex 32)"
echo "NOMOS_PLUGIN_API_KEY=$(openssl rand -hex 24)"
echo "NOMOS_GATEWAY_TOKEN=$(openssl rand -hex 24)"
echo "NOMOS_DB_PASSWORD=$(openssl rand -hex 16)"
```

Paste the output values into your `.env` file.

Set at least one LLM provider key (NVIDIA has a free tier at https://build.nvidia.com):

```
NVIDIA_API_KEY=nvapi-your-key-here
# or: ANTHROPIC_API_KEY=sk-ant-...
# or: OPENAI_API_KEY=sk-...
```

### Recommended additional secret

| Variable | Description |
|---|---|
| `NOMOS_HASHCHAIN_HMAC_KEY` | HMAC key for the tamper-evident audit chain. Set this (inject from Vault in production) — without it the chain falls back to plain SHA-256. Read by `nomos-cli/nomos/core/hash_chain.py:30-43`. |

### Optional runtime tuning (non-secret)

| Variable | Default | Description |
|---|---|---|
| `NOMOS_LOG_LEVEL` | `INFO` | CLI diagnostics verbosity: `DEBUG`/`INFO`/`WARNING`/`ERROR` (case-insensitive). Invalid values fall back to `INFO` with a warning. JSON diagnostics go to **stderr**; normal CLI output stays on stdout. |
| `NOMOS_VALKEY_URL` | `valkey://valkey:6379` | Valkey URL (rate limiting + ARQ worker). |
| `NOMOS_DEV_MODE` | `false` | Keep `false` in production. |
| `NOMOS_COOKIE_SECURE` | `true` | Secure-cookie + HSTS toggle. |
| `NOMOS_DOMAIN` | `localhost` | Public domain for Caddy automatic TLS. |

> **OpenClaw pin:** the gateway image is pinned to the current stable
> release `2026.5.18` in `nomos-plugin/Dockerfile.gateway:1` (never
> `:latest`). Earlier docs referenced `v2026.3.28`; the running pin is
> the authoritative version.

## 2. Start NomOS

```bash
docker compose up -d
```

NomOS starts 8 services. Wait for all to become healthy (takes ~60 seconds on first run):

```bash
docker compose ps
```

All services should show `healthy` or `running`:

| Service | Port | Purpose |
|---|---|---|
| `caddy` | 80 / 443 | Reverse proxy with automatic TLS |
| `nomos-console` | `${NOMOS_CONSOLE_PORT:-3040}` | Next.js dashboard |
| `nomos-api` | `${NOMOS_API_PORT:-8060}` | FastAPI control plane |
| `nomos-worker` | — | ARQ background job processor (no host port) |
| `openclaw-gateway` | `${NOMOS_GATEWAY_PORT:-3050}` | Headless plugin framework |
| `postgres` | — | PostgreSQL 16 + pgvector (compose-internal, no host port) |
| `valkey` | — | Cache + rate limiting + ARQ broker (compose-internal, no host port) |
| `vault` | 8200 | HashiCorp Vault secret management |

> Ports are per `docker-compose.yml` (`:3,13-14,90-91,166-167`,
> `185-202`). `postgres` and `valkey` are not host-published.

Verify the API is healthy:

```bash
curl http://localhost:8060/health
```

Expected response (shape per `routers/health.py:71-87` —
`HealthResponse` with per-component statuses):

```json
{
  "status": "healthy",
  "service": "NomOS Fleet API",
  "version": "0.2.1",
  "vault": "healthy",
  "components": { "vault": "healthy", "postgres": "healthy",
                  "valkey": "healthy", "gateway": "online" }
}
```

`status` is `healthy` only when PostgreSQL is reachable, otherwise
`degraded`. The gateway being `offline` does not by itself fail the
health check.

## 3. First Login

Open **http://localhost:3040** in your browser.

On first launch, the console shows a **Bootstrap** screen. Create your admin account:

```bash
curl -X POST http://localhost:8060/api/users/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "a-strong-passphrase",
    "role": "admin"
  }'
```

Or fill in the bootstrap form in the browser. The response includes a
one-time **recovery phrase** — store it safely; it is the only way back
in if 2FA is lost. After bootstrap, log in with your credentials.

> **Note:** The bootstrap endpoint is `POST /api/users/bootstrap`
> (`routers/users.py:66`). It only works while no users exist and
> returns **403** afterwards. The password must pass strength
> validation (`422` otherwise).

## 4. Configure LLM Provider

1. Click **Settings** in the left sidebar
2. Open the **LLM Provider** section
3. Enter your API key (NVIDIA / Anthropic / OpenAI)
4. Select a default model
5. Click **Save**

NomOS is provider-agnostic. You can switch providers or add multiple keys at any time.

## 5. Hire Your First Agent

Click **Hire** in the sidebar or navigate to **http://localhost:3040/hire**.

The Hire wizard walks you through four steps:

1. **Identity** — Name, role, and company (e.g. `Support Assistant`, `customer-support`, `Acme GmbH`)
2. **Capabilities** — Select what the agent is allowed to do (web search, file access, code execution)
3. **Risk Classification** — Choose the EU AI Act risk class (`minimal`, `limited`, `high`)
4. **Review** — Inspect the generated compliance documents before deploying

Click **Deploy Agent**. NomOS automatically generates the required EU AI Act compliance documents:

- DPIA (Art. 35 GDPR)
- Records of Processing Activities (Art. 30 GDPR)
- Transparency Declaration (Art. 50 EU AI Act)
- Human Oversight / Kill Switch Policy (Art. 14 EU AI Act)
- Record-Keeping / Logging Policy (Art. 12 EU AI Act)

## 6. Start Chatting

1. Open the **Fleet** view — your new agent appears with compliance status `COMPLIANT`
2. Click the agent name to open the detail view
3. Click **Chat** in the top right
4. Send a message — the agent responds via the configured LLM provider

The audit trail records every interaction automatically.

## Troubleshooting

**"Not compliant" status** — This can occur if compliance document generation is still in progress. Wait a few seconds and refresh. If it persists, open the agent detail view and click **Run Compliance Gate**.

**Chat not responding** — Check that an LLM provider key is configured in Settings. Verify the key is valid by testing it directly with the provider's API.

**502 Bad Gateway errors** — The OpenClaw gateway may still be starting. Check its logs:
```bash
docker logs nomos-openclaw-gateway-1 --tail 50
```

**Services not starting** — View logs for all services:
```bash
docker compose logs -f
```
For a specific service: `docker compose logs -f nomos-api`

**Port conflicts** — If ports 80, 443, 3040, or 8060 are in use, configure alternatives in `.env`:
```
NOMOS_HTTP_PORT=8080
NOMOS_HTTPS_PORT=8443
NOMOS_CONSOLE_PORT=3041
NOMOS_API_PORT=8061
```

**Vault not initializing** — On first run, Vault needs to be initialized. Check:
```bash
docker compose logs vault --tail 30
```

**docker compose fails immediately with "Set NOMOS_DB_PASSWORD in .env"**
— A required secret is unset. `docker-compose.yml` uses
`${NOMOS_DB_PASSWORD:?...}` and similar guards, so compose refuses to
start until the required secrets from Step 1 are set in `.env` (the
shipped `.env.example` ships placeholder values such as
`your_secure_password_here` that must be replaced).

---

## Next Steps

- [API Reference](api-reference.md) — all REST endpoints
- [Compliance Guide](compliance-guide.md) — EU AI Act coverage in detail
- [Architecture](architecture.md) — system design and data flow
- [Operations Runbook](operations-runbook.md) — bring-up order, backups, troubleshooting
- [CLI Reference](cli-reference.md) — command-line interface for automation
