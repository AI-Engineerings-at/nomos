#!/usr/bin/env bash
# NomOS E2E Test — verifies the full stack works end-to-end.
set -euo pipefail

API_URL="http://localhost:${NOMOS_API_PORT:-8060}"
CONSOLE_URL="http://localhost:${NOMOS_CONSOLE_PORT:-3040}"
PASSED=0
FAILED=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
    local name="$1" url="$2" expected="${3:-200}" method="${4:-GET}" data="${5:-}"
    if [ -n "$data" ]; then
        status=$(curl -sf -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "000")
    else
        status=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    fi
    if [ "$status" = "$expected" ]; then
        echo -e "  ${GREEN}PASS${NC} $name (HTTP $status)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} $name (expected $expected, got $status)"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== NomOS E2E Test ==="
echo ""
echo "Starting stack..."
docker compose up -d --build --wait 2>&1 || true
sleep 5
echo ""

echo "--- Health ---"
check "API /health" "$API_URL/health"
check "Console /" "$CONSOLE_URL/"

echo ""
echo "--- Fleet (empty) ---"
check "GET /api/fleet" "$API_URL/api/fleet"

echo ""
echo "--- Create Agent ---"
check "POST /api/agents" "$API_URL/api/agents" "201" "POST" '{"name":"E2E Test","role":"test","company":"Test GmbH","email":"test@test.at"}'

echo ""
echo "--- Verify ---"
check "GET /api/fleet (1 agent)" "$API_URL/api/fleet"
check "GET compliance" "$API_URL/api/agents/e2e-test/compliance"
check "GET audit" "$API_URL/api/agents/e2e-test/audit"
check "GET verify chain" "$API_URL/api/audit/verify/e2e-test"

echo ""
echo "=== Results: PASSED=$PASSED FAILED=$FAILED ==="

echo "Stopping stack..."
docker compose down -v 2>&1 || true

exit "$FAILED"
