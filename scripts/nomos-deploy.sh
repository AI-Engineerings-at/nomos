#!/usr/bin/env bash
# NomOS Deploy Script — docker compose up on customer server
# Usage: ./scripts/nomos-deploy.sh [--with-speech]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "  NomOS v2 — Deployment"
echo "  ====================="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not installed"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "ERROR: Docker Compose not installed"; exit 1; }

# Parse args
PROFILE_FLAGS=""
if [[ "${1:-}" == "--with-speech" ]]; then
  PROFILE_FLAGS="--profile speech"
  echo "  Speech services (Piper TTS + Whisper STT) enabled"
fi

# Check .env
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  echo "  Creating .env from .env.example..."
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  echo "  IMPORTANT: Edit .env and set NOMOS_JWT_SECRET before production use!"
fi

# Deploy
echo ""
echo "  Starting NomOS stack..."
cd "$PROJECT_DIR"
docker compose $PROFILE_FLAGS up -d --build

echo ""
echo "  Waiting for services..."
sleep 5

# Health check
API_URL="http://localhost:${NOMOS_API_PORT:-8060}"
if curl -sf "$API_URL/health" >/dev/null 2>&1; then
  echo "  API:     OK ($API_URL)"
else
  echo "  API:     STARTING (may take a moment)"
fi

CONSOLE_URL="http://localhost:${NOMOS_CONSOLE_PORT:-3040}"
echo "  Console: $CONSOLE_URL"

echo ""
echo "  NomOS is running."
echo "  Open $CONSOLE_URL in your browser."
echo ""
