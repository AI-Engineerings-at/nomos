#!/usr/bin/env sh
set -e

# Read gateway token from vault-init output if not set via ENV
if [ -z "$NOMOS_GATEWAY_TOKEN" ] && [ -f /vault/init/gateway-token ]; then
  export NOMOS_GATEWAY_TOKEN=$(cat /vault/init/gateway-token)
  echo "==> Gateway token loaded from Vault init volume."
fi

# Read plugin API key from vault-init output if not set via ENV
if [ -z "$NOMOS_PLUGIN_API_KEY" ] && [ -f /vault/init/plugin-api-key ]; then
  export NOMOS_PLUGIN_API_KEY=$(cat /vault/init/plugin-api-key)
  echo "==> Plugin API key loaded from Vault init volume."
fi

# Replace environment variables in openclaw.json
# Uses a temporary file to avoid issues with reading/writing to the same file
if [ -f /home/node/.openclaw/openclaw.json ]; then
  echo "==> Substituting environment variables in openclaw.json..."
  # Create a template if it doesn't exist (on first run or if mounted as file)
  # But wait, if it's mounted as :ro, we can't edit it in place.
  # We should copy it to a writable location first.
  cp /home/node/.openclaw/openclaw.json /tmp/openclaw.json.tmp
  
  # Simple substitution using sed (since envsubst might not be available)
  # This only handles NOMOS_GATEWAY_TOKEN
  sed "s/\${NOMOS_GATEWAY_TOKEN}/${NOMOS_GATEWAY_TOKEN}/g" /tmp/openclaw.json.tmp > /home/node/.openclaw/openclaw.json.actual
  
  # Point OpenClaw to the actual config
  export OPENCLAW_CONFIG_PATH=/home/node/.openclaw/openclaw.json.actual
fi

# Execute the original entrypoint/command
exec "$@"
