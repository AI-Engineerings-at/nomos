#!/usr/bin/env sh
# vault/init.sh — Idempotent Vault bootstrap for NomOS
# WARNING: This uses a single unseal key with threshold 1.
# For production, use KMS auto-unseal (AWS KMS, Azure Key Vault, GCP CKMS).
set -e

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_ADDR

CREDS_DIR="/vault/file"
INIT_FILE="${CREDS_DIR}/init-output.json"
APPROLE_FILE="${CREDS_DIR}/approle-creds.env"

echo "==> Waiting for Vault to be available..."
until vault status -format=json 2>/dev/null | jq -e '.initialized != null' > /dev/null 2>&1; do
  sleep 1
done
echo "==> Vault is available."

# --- Initialize if not initialized ---
INITIALIZED=$(vault status -format=json | jq -r '.initialized')
if [ "$INITIALIZED" = "false" ]; then
  echo "==> Initializing Vault (1 key share, 1 threshold)..."
  vault operator init -key-shares=1 -key-threshold=1 -format=json > "$INIT_FILE"
  chmod 600 "$INIT_FILE"
  echo "==> Vault initialized. Keys stored in ${INIT_FILE}"
fi

# --- Read unseal key and root token ---
UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' "$INIT_FILE")
ROOT_TOKEN=$(jq -r '.root_token' "$INIT_FILE")
export VAULT_TOKEN="$ROOT_TOKEN"

# --- Unseal if sealed ---
SEALED=$(vault status -format=json | jq -r '.sealed')
if [ "$SEALED" = "true" ]; then
  echo "==> Unsealing Vault..."
  vault operator unseal "$UNSEAL_KEY" > /dev/null
  echo "==> Vault unsealed."
fi

# --- Enable KV v2 at nomos/ (idempotent) ---
if ! vault secrets list -format=json | jq -e '."nomos/"' > /dev/null 2>&1; then
  echo "==> Enabling KV v2 at nomos/..."
  vault secrets enable -path=nomos kv-v2
else
  echo "==> KV v2 at nomos/ already enabled."
fi

# --- Write nomos-api policy ---
echo "==> Writing nomos-api policy..."
vault policy write nomos-api /vault/policies/nomos-api.hcl

# --- Enable AppRole auth (idempotent) ---
if ! vault auth list -format=json | jq -e '."approle/"' > /dev/null 2>&1; then
  echo "==> Enabling AppRole auth..."
  vault auth enable approle
else
  echo "==> AppRole auth already enabled."
fi

# --- Create nomos-api role ---
echo "==> Creating nomos-api AppRole..."
vault write auth/approle/role/nomos-api \
  token_policies="nomos-api" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0

# --- Get role_id and secret_id ---
ROLE_ID=$(vault read -format=json auth/approle/role/nomos-api/role-id | jq -r '.data.role_id')
SECRET_ID=$(vault write -format=json -f auth/approle/role/nomos-api/secret-id | jq -r '.data.secret_id')

cat > "$APPROLE_FILE" <<EOF
VAULT_ROLE_ID=${ROLE_ID}
VAULT_SECRET_ID=${SECRET_ID}
EOF
chmod 600 "$APPROLE_FILE"

echo "==> AppRole credentials written to ${APPROLE_FILE}"
echo "==> Vault bootstrap complete."
