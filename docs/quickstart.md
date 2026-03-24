# NomOS Quickstart

Get NomOS running and create your first compliant AI agent in 5 minutes.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for CLI only)
- curl (for testing)

## 1. Clone the Repository

```bash
git clone https://github.com/ai-engineering-at/nomos.git
cd nomos
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set a secure database password:

```
NOMOS_DB_PASSWORD=your-secure-password
NOMOS_API_PORT=8060
NOMOS_CONSOLE_PORT=3040
```

## 3. Start the Stack

```bash
docker compose up -d
```

This starts three services:
- **nomos-api** on `http://localhost:8060` (FastAPI REST API)
- **nomos-console** on `http://localhost:3040` (Next.js dashboard)
- **PostgreSQL 16** with pgvector (internal, not exposed)

Wait for all services to be healthy:

```bash
docker compose ps
```

Verify the API is running:

```bash
curl http://localhost:8060/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "NomOS Fleet API",
  "version": "0.1.0"
}
```

## 4. Create Your First Agent

```bash
curl -X POST http://localhost:8060/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mani Ruf",
    "role": "external-secretary",
    "company": "Acme GmbH",
    "email": "mani@acme.at",
    "risk_class": "limited"
  }'
```

The response shows the new agent with `compliance_status: "blocked"` — this is expected. The agent has no compliance documents yet.

## 5. Run the Compliance Gate

Generate all 5 required compliance documents:

```bash
curl -X POST http://localhost:8060/api/agents/mani-ruf/gate
```

Expected response:

```json
{
  "agent_id": "mani-ruf",
  "status": "passed",
  "missing_documents": [],
  "errors": [],
  "warnings": []
}
```

The gate generates:
- DPIA (Art. 35 DSGVO)
- Verarbeitungsverzeichnis (Art. 30 DSGVO)
- Transparency Declaration (Art. 50 EU AI Act)
- Human Oversight / Kill Switch Policy (Art. 14 EU AI Act)
- Record-Keeping / Logging Policy (Art. 12 EU AI Act)

## 6. Check in the Dashboard

Open `http://localhost:3040` in your browser. You should see:

- Fleet overview with your agent listed
- Agent detail view with manifest data
- Compliance status: PASSED
- Audit trail showing the creation event

## 7. View the Audit Trail

```bash
curl http://localhost:8060/api/agents/mani-ruf/audit
```

This returns all audit entries for the agent, including the creation event with its hash chain entry.

## 8. Verify Chain Integrity

```bash
curl http://localhost:8060/api/audit/verify/mani-ruf
```

Expected response:

```json
{
  "agent_id": "mani-ruf",
  "valid": true,
  "entries_checked": 1,
  "errors": []
}
```

This cryptographically verifies that no audit entries have been tampered with.

---

## Using the CLI Instead

If you prefer working locally without Docker:

```bash
cd nomos-cli
pip install -e .
```

### Create an agent

```bash
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf
```

### Generate compliance documents

```bash
nomos gate --agent-dir ./data/agents/mani-ruf
```

### Verify compliance

```bash
nomos verify --agent-dir ./data/agents/mani-ruf
```

### List all agents

```bash
nomos fleet --agents-dir ./data/agents
```

### View audit trail

```bash
nomos audit --agent-dir ./data/agents/mani-ruf
```

### Verify audit chain integrity

```bash
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

---

## Next Steps

- Read the [API Reference](api-reference.md) for all endpoints
- Read the [Compliance Guide](compliance-guide.md) to understand EU AI Act coverage
- Read the [CLI Reference](cli-reference.md) for all commands and flags
- Read the [Architecture](architecture.md) for system design details
