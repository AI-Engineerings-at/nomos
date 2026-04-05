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
| `nomos-console` | 3040 | Next.js dashboard |
| `nomos-api` | 8060 | FastAPI control plane |
| `nomos-worker` | — | Background job processor |
| `openclaw-gateway` | 3050 | Headless plugin framework |
| `postgres` | — | PostgreSQL 16 + pgvector (internal) |
| `valkey` | 6380 | Cache and rate limiting (internal) |
| `vault` | 8200 | HashiCorp Vault secret management |

Verify the API is healthy:

```bash
curl http://localhost:8060/health
```

Expected response:

```json
{"status": "ok", "service": "NomOS API"}
```

## 3. First Login

Open **http://localhost:3040** in your browser.

On first launch, the console shows a **Bootstrap** screen. Create your admin account:

```bash
curl -X POST http://localhost:8060/api/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "change-me-now"
  }'
```

Or fill in the bootstrap form in the browser. After bootstrap, log in with your credentials.

> **Note:** The bootstrap endpoint is only available when no users exist. It disables itself after first use.

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

**docker compose fails immediately** — You have placeholder values in `.env`. Replace all `CHANGE_ME_REQUIRED_*` values with real secrets (see Step 1).

---

## Next Steps

- [API Reference](api-reference.md) — all REST endpoints
- [Compliance Guide](compliance-guide.md) — EU AI Act coverage in detail
- [Architecture](architecture.md) — system design and data flow
- [CLI Reference](cli-reference.md) — command-line interface for automation
