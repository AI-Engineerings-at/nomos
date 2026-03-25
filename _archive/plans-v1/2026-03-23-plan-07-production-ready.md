# Plan 7: Production-Ready Stack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make NomOS deployable with a single `docker compose up -d` at the repo root — API, Console, PostgreSQL, Redis all running, connected, and health-checked. A customer clones the repo and has a working compliance platform.

**Architecture:** Master docker-compose.yml at repo root orchestrates all services. Console talks to API via internal Docker network. API talks to PostgreSQL. Everything configurable via .env. An E2E test script verifies the full stack after startup.

**Tech Stack:** Docker Compose, Python 3.12, Node.js 22, PostgreSQL 16, Redis 8

---

## File Structure

### Files to CREATE

```
docker-compose.yml                  # Master stack: API + Console + Postgres + Redis
.env.example                        # All configurable env vars with safe defaults
scripts/
├── e2e-test.sh                     # E2E test: start stack → test endpoints → verify → stop
└── wait-for-healthy.sh             # Wait for all services to be healthy
```

### Files to MODIFY

```
nomos-console/Dockerfile            # Fix standalone path (COPY --from=builder)
nomos-api/Dockerfile                # Add curl for healthcheck
.github/workflows/ci.yml            # Add docker-build job
.gitignore                          # Add .env to ignore list (already done, verify)
```

---

## Task 1: Master docker-compose.yml

**Why:** The customer runs ONE command. Not `cd nomos-api && docker compose up`, but `docker compose up` at the root.

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create docker-compose.yml at repo root**

```yaml
services:
  nomos-api:
    build:
      context: .
      dockerfile: nomos-api/Dockerfile
    ports:
      - "${NOMOS_API_PORT:-8060}:8000"
    environment:
      - NOMOS_DATABASE_URL=postgresql+asyncpg://nomos:${NOMOS_DB_PASSWORD:-nomos}@postgres:5432/nomos
      - NOMOS_AGENTS_DIR=/data/agents
      - NOMOS_CORS_ORIGINS=["http://localhost:${NOMOS_CONSOLE_PORT:-3040}"]
    volumes:
      - nomos-agents:/data/agents
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  nomos-console:
    build:
      context: .
      dockerfile: nomos-console/Dockerfile
    ports:
      - "${NOMOS_CONSOLE_PORT:-3040}:3040"
    environment:
      - NEXT_PUBLIC_API_URL=http://nomos-api:8000
    depends_on:
      nomos-api:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3040').then(r=>{if(!r.ok)throw 1})"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=nomos
      - POSTGRES_USER=nomos
      - POSTGRES_PASSWORD=${NOMOS_DB_PASSWORD:-nomos}
    volumes:
      - nomos-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nomos"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:8-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  nomos-pgdata:
  nomos-agents:
```

- [ ] **Step 2: Create .env.example**

```bash
# NomOS Configuration
# Copy to .env and adjust for your environment

# Database
NOMOS_DB_PASSWORD=change-me-in-production

# Ports
NOMOS_API_PORT=8060
NOMOS_CONSOLE_PORT=3040
```

- [ ] **Step 3: Verify .env is in .gitignore**

Check that `.env` (without example) is gitignored:
```bash
grep "^\.env$" .gitignore || echo ".env" >> .gitignore
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example .gitignore
git commit -m "feat: master docker-compose.yml — one command to start everything

docker compose up -d starts: API (:8060) + Console (:3040) + PostgreSQL + Redis.
All configurable via .env (copy from .env.example).
Health checks on all services. Console waits for API, API waits for Postgres."
```

---

## Task 2: Fix Dockerfiles

**Why:** Both Dockerfiles need small fixes to work in the master compose context (build context = repo root).

**Files:**
- Modify: `nomos-api/Dockerfile`
- Modify: `nomos-console/Dockerfile`

- [ ] **Step 1: Fix nomos-api Dockerfile — add curl for healthcheck**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY nomos-cli /app/nomos-cli
COPY nomos-api/pyproject.toml /app/
COPY nomos-api/nomos_api /app/nomos_api/

ENV PYTHONPATH="/app/nomos-cli:${PYTHONPATH}"

RUN uv pip install --system "."

EXPOSE 8000

CMD ["uvicorn", "nomos_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Note: Changed `".[dev]"` to `"."` — production image should NOT install dev dependencies.

- [ ] **Step 2: Fix nomos-console Dockerfile — correct standalone paths**

The Next.js standalone output goes to `.next/standalone/` but the server.js path depends on the working directory during build. Check and fix:

```dockerfile
FROM node:22-slim AS builder

WORKDIR /app
COPY nomos-console/package.json nomos-console/package-lock.json* ./
RUN npm ci
COPY nomos-console/ .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3040
ENV HOSTNAME="0.0.0.0"

# Copy standalone output — includes server.js + node_modules
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# Copy public assets if they exist
COPY --from=builder /app/public ./public 2>/dev/null || true

EXPOSE 3040
CMD ["node", "server.js"]
```

- [ ] **Step 3: Test both builds**

```bash
cd /path/to/nomos
docker compose build
```

Expected: Both images build successfully.

- [ ] **Step 4: Commit**

```bash
git add nomos-api/Dockerfile nomos-console/Dockerfile
git commit -m "fix: Dockerfiles — add curl for healthcheck, fix standalone paths

API: install curl for health checks, production deps only (not dev).
Console: set HOSTNAME for Next.js standalone, correct static file copy."
```

---

## Task 3: E2E Test Script

**Why:** A senior dev doesn't say "it works" — they have a script that PROVES it works. This script starts the stack, waits for health, tests every endpoint, and reports pass/fail.

**Files:**
- Create: `scripts/e2e-test.sh`

- [ ] **Step 1: Create the E2E test script**

```bash
#!/usr/bin/env bash
# NomOS E2E Test — verifies the full stack works end-to-end.
# Usage: ./scripts/e2e-test.sh
#
# Starts docker compose, waits for health, tests all endpoints,
# cleans up. Exit 0 = all pass, exit 1 = failures.

set -euo pipefail

API_URL="http://localhost:${NOMOS_API_PORT:-8060}"
CONSOLE_URL="http://localhost:${NOMOS_CONSOLE_PORT:-3040}"
PASSED=0
FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"
    local data="${5:-}"

    if [ -n "$data" ]; then
        status=$(curl -sf -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "000")
    else
        status=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$status" = "$expected_status" ]; then
        echo -e "  ${GREEN}PASS${NC} $name (HTTP $status)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} $name (expected $expected_status, got $status)"
        FAILED=$((FAILED + 1))
    fi
}

check_json() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    local expected="$4"

    actual=$(curl -sf "$url" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print($jq_filter)" 2>/dev/null || echo "ERROR")

    if [ "$actual" = "$expected" ]; then
        echo -e "  ${GREEN}PASS${NC} $name ($actual)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} $name (expected '$expected', got '$actual')"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== NomOS E2E Test ==="
echo ""

# 1. Start stack
echo "Starting stack..."
docker compose up -d --build --wait 2>/dev/null
echo "Stack started."
echo ""

# 2. Health checks
echo "--- Health Checks ---"
check "API /health" "$API_URL/health"
check "Console /" "$CONSOLE_URL/"
check_json "API service name" "$API_URL/health" "d['service']" "NomOS Fleet API"

# 3. Fleet (empty)
echo ""
echo "--- Fleet (empty) ---"
check "GET /api/fleet" "$API_URL/api/fleet"
check_json "Fleet is empty" "$API_URL/api/fleet" "d['total']" "0"

# 4. Create agent
echo ""
echo "--- Create Agent ---"
check "POST /api/agents" "$API_URL/api/agents" "201" "POST" '{"name":"E2E Test Agent","role":"test","company":"Test GmbH","email":"test@test.at"}'

# 5. Fleet (1 agent)
echo ""
echo "--- Fleet (1 agent) ---"
check_json "Fleet has 1 agent" "$API_URL/api/fleet" "d['total']" "1"
check_json "Agent name correct" "$API_URL/api/fleet" "d['agents'][0]['name']" "E2E Test Agent"

# 6. Compliance check
echo ""
echo "--- Compliance ---"
check "GET compliance" "$API_URL/api/agents/e2e-test-agent/compliance"
check_json "Compliance status" "$API_URL/api/agents/e2e-test-agent/compliance" "d['status']" "blocked"

# 7. Audit trail
echo ""
echo "--- Audit Trail ---"
check "GET audit" "$API_URL/api/agents/e2e-test-agent/audit"
check_json "Audit has entries" "$API_URL/api/agents/e2e-test-agent/audit" "d['total']" "1"
check_json "First event is agent.created" "$API_URL/api/agents/e2e-test-agent/audit" "d['entries'][0]['event_type']" "agent.created"

# 8. Chain verification
echo ""
echo "--- Chain Verification ---"
check "GET audit verify" "$API_URL/api/audit/verify/e2e-test-agent"
check_json "Chain is valid" "$API_URL/api/audit/verify/e2e-test-agent" "d['valid']" "True"

# 9. Console serves HTML
echo ""
echo "--- Console ---"
check "Console homepage" "$CONSOLE_URL/"

# Summary
echo ""
echo "=== Results ==="
echo -e "  ${GREEN}PASSED: $PASSED${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "  ${RED}FAILED: $FAILED${NC}"
fi
echo ""

# Cleanup
echo "Stopping stack..."
docker compose down -v 2>/dev/null
echo "Done."

exit "$FAILED"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/e2e-test.sh
```

- [ ] **Step 3: Run it**

```bash
cd /path/to/nomos
./scripts/e2e-test.sh
```

Expected: All checks PASS, exit 0.

- [ ] **Step 4: Commit**

```bash
git add scripts/
git commit -m "test(e2e): full stack test script — proves everything works

Starts docker compose, waits for health, tests all 7 API endpoints,
verifies agent creation + compliance + audit chain + console.
Cleans up after. Exit 0 = all pass."
```

---

## Task 4: CI Docker Build Job

**Why:** CI must verify the Docker images build. If they break, we know before customers do.

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add docker-build job**

Read current ci.yml, then add:

```yaml
  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [test-cli, test-api]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - run: docker compose build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add docker-build job — verify images build on every push"
```

---

## Task 5: Final Verification + Push

- [ ] **Step 1: Run unit tests (both packages)**

```bash
cd nomos-cli && uv run pytest -v --tb=short
cd ../nomos-api && PYTHONPATH="../nomos-cli" uv run pytest -v --tb=short
```

- [ ] **Step 2: Run E2E test**

```bash
./scripts/e2e-test.sh
```

- [ ] **Step 3: S9 + R12 checks**

```bash
grep -r "coming soon\|TODO\|FIXME\|placeholder" nomos-cli/nomos/ nomos-api/nomos_api/ nomos-console/src/ || echo "S9: CLEAN"
grep -r "10.40.10" nomos-cli/ nomos-api/ nomos-console/src/ nomos-plugin/src/ || echo "R12: CLEAN"
```

- [ ] **Step 4: Push**

```bash
git push origin main
```

---

## Summary

After Plan 7 completion:

| What | Status |
|------|--------|
| `docker compose up -d` at repo root | Works — API + Console + Postgres + Redis |
| E2E test script | Proves all endpoints + console + audit chain |
| Customer experience | Clone → copy .env.example → docker compose up → done |
| CI | Unit tests + API tests + Docker build |
| **Total tests** | 97 unit + 14 E2E checks = 111 verified behaviors |

**The product is shippable after this plan.**
