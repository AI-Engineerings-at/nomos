#!/usr/bin/env sh
# vault/init-entrypoint.sh — Idempotent Vault bootstrap for NomOS
# Runs as a one-shot init container: init, unseal, seed secrets, write AppRole creds, exit.
# WARNING: Uses a single unseal key with threshold 1.
# For production, use KMS auto-unseal (AWS KMS, Azure Key Vault, GCP CKMS).
set -e

VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
export VAULT_ADDR

# --- Directories ---
# /vault/file is the persistent Vault storage (shared with vault server).
# /vault/init is the shared init volume for passing creds to nomos-api/worker.
VAULT_STORAGE="/vault/file"
INIT_DIR="/vault/init"
INIT_FILE="${VAULT_STORAGE}/init-output.json"
APPROLE_FILE="${INIT_DIR}/approle-creds.env"
INITIALIZED_MARKER="${INIT_DIR}/initialized"

mkdir -p "${INIT_DIR}"

echo "==> Waiting for Vault to be available at ${VAULT_ADDR}..."
until vault status -format=json 2>/dev/null | jq -e '.initialized != null' > /dev/null 2>&1; do
  sleep 1
done
echo "==> Vault is available."

# ─── Phase 1: Initialize if not initialized ─────────────────
INITIALIZED=$(vault status -format=json | jq -r '.initialized')
if [ "${INITIALIZED}" = "false" ]; then
  echo "==> Initializing Vault (1 key share, 1 threshold)..."
  vault operator init -key-shares=1 -key-threshold=1 -format=json > "${INIT_FILE}"
  chmod 600 "${INIT_FILE}"
  echo "==> Vault initialized. Keys stored in ${INIT_FILE}"
fi

# ─── Phase 2: Read credentials and unseal ────────────────────
if [ ! -f "${INIT_FILE}" ]; then
  echo "FATAL: Init file ${INIT_FILE} not found. Cannot unseal."
  exit 1
fi

UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' "${INIT_FILE}")
ROOT_TOKEN=$(jq -r '.root_token' "${INIT_FILE}")
export VAULT_TOKEN="${ROOT_TOKEN}"

SEALED=$(vault status -format=json | jq -r '.sealed')
if [ "${SEALED}" = "true" ]; then
  echo "==> Unsealing Vault..."
  vault operator unseal "${UNSEAL_KEY}" > /dev/null
  echo "==> Vault unsealed."
else
  echo "==> Vault already unsealed."
fi

# ─── Phase 3: Enable KV v2 at nomos/ (idempotent) ───────────
if ! vault secrets list -format=json | jq -e '."nomos/"' > /dev/null 2>&1; then
  echo "==> Enabling KV v2 at nomos/..."
  vault secrets enable -path=nomos kv-v2
else
  echo "==> KV v2 at nomos/ already enabled."
fi

# ─── Phase 4: Write nomos-api policy ────────────────────────
echo "==> Writing nomos-api policy..."
vault policy write nomos-api /vault/policies/nomos-api.hcl

# ─── Phase 5: Enable AppRole auth (idempotent) ──────────────
if ! vault auth list -format=json | jq -e '."approle/"' > /dev/null 2>&1; then
  echo "==> Enabling AppRole auth..."
  vault auth enable approle
else
  echo "==> AppRole auth already enabled."
fi

# ─── Phase 6: Create nomos-api AppRole ───────────────────────
echo "==> Creating nomos-api AppRole..."
vault write auth/approle/role/nomos-api \
  token_policies="nomos-api" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0

# ─── Phase 7: Generate and store system secrets ─────────────
# Only generate on first init. On subsequent runs, secrets already exist in Vault.
if [ ! -f "${INITIALIZED_MARKER}" ]; then
  echo "==> Generating system secrets (first run)..."

  # Generate cryptographically secure secrets
  JWT_SECRET=$(openssl rand -base64 48)
  PLUGIN_API_KEY="npk-$(openssl rand -hex 24)"
  GATEWAY_TOKEN="gw-$(openssl rand -hex 24)"

  echo "==> Storing system secrets in Vault..."
  vault kv put nomos/secrets/system \
    jwt_secret="${JWT_SECRET}" \
    plugin_api_key="${PLUGIN_API_KEY}" \
    gateway_token="${GATEWAY_TOKEN}"

  echo "==> Storing database credentials in Vault..."
  vault kv put nomos/secrets/database \
    password="${NOMOS_DB_PASSWORD:-changeme}"
else
  echo "==> System secrets already exist (marker found). Verifying..."
  if vault kv get nomos/secrets/system > /dev/null 2>&1; then
    echo "==> System secrets verified in Vault."
  else
    echo "WARNING: Marker exists but secrets not found. Re-creating..."
    JWT_SECRET=$(openssl rand -base64 48)
    PLUGIN_API_KEY="npk-$(openssl rand -hex 24)"
    GATEWAY_TOKEN="gw-$(openssl rand -hex 24)"

    vault kv put nomos/secrets/system \
      jwt_secret="${JWT_SECRET}" \
      plugin_api_key="${PLUGIN_API_KEY}" \
      gateway_token="${GATEWAY_TOKEN}"

    vault kv put nomos/secrets/database \
      password="${NOMOS_DB_PASSWORD:-changeme}"
  fi
fi

# ─── Phase 8: Get AppRole credentials ───────────────────────
ROLE_ID=$(vault read -format=json auth/approle/role/nomos-api/role-id | jq -r '.data.role_id')
SECRET_ID=$(vault write -format=json -f auth/approle/role/nomos-api/secret-id | jq -r '.data.secret_id')

cat > "${APPROLE_FILE}" <<EOF
VAULT_ROLE_ID=${ROLE_ID}
VAULT_SECRET_ID=${SECRET_ID}
EOF
chmod 600 "${APPROLE_FILE}"

# ─── Phase 9: Write initialized marker ──────────────────────
touch "${INITIALIZED_MARKER}"
chmod 600 "${INITIALIZED_MARKER}"

echo "==> AppRole credentials written to ${APPROLE_FILE}"
echo "==> Vault bootstrap complete. Exiting."
exit 0
