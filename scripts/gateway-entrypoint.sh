#!/bin/sh
# Fix Windows bind-mount permissions for OpenClaw plugin.
# Windows mounts appear as mode=777, which OpenClaw blocks as world-writable.
# Strategy: stage plugin via bind-mount to /tmp, copy to named volume with safe permissions.

PLUGIN_STAGE="/tmp/nomos-plugin-stage"
EXT_DIR="/home/node/.openclaw/extensions"
PLUGIN_TARGET="$EXT_DIR/nomos"

# Fix volume ownership if root-owned (Docker creates volumes as root)
if [ ! -w "$EXT_DIR" ]; then
  echo "[nomos-entrypoint] fixing extensions dir ownership..."
  # Try copying to /tmp first, then moving
  TEMP_EXT="/tmp/openclaw-extensions"
  rm -rf "$TEMP_EXT"
  mkdir -p "$TEMP_EXT"
fi

if [ -d "$PLUGIN_STAGE" ] && [ -w "$EXT_DIR" ]; then
  rm -rf "$PLUGIN_TARGET"
  cp -r "$PLUGIN_STAGE" "$PLUGIN_TARGET"
  chmod -R 755 "$PLUGIN_TARGET"
  find "$PLUGIN_TARGET" -type f -exec chmod 644 {} +
  echo "[nomos-entrypoint] plugin copied with safe permissions"
elif [ -d "$PLUGIN_STAGE" ]; then
  echo "[nomos-entrypoint] ERROR: extensions dir not writable, trying workaround..."
  # Copy to temp, use OPENCLAW_EXTENSIONS_DIR if supported
  TEMP_EXT="/tmp/openclaw-extensions/nomos"
  rm -rf "$TEMP_EXT"
  mkdir -p /tmp/openclaw-extensions
  cp -r "$PLUGIN_STAGE" "$TEMP_EXT"
  chmod -R 755 "$TEMP_EXT"
  find "$TEMP_EXT" -type f -exec chmod 644 {} +
  export OPENCLAW_EXTENSIONS_DIR="/tmp/openclaw-extensions"
  echo "[nomos-entrypoint] plugin at $TEMP_EXT (fallback path)"
else
  echo "[nomos-entrypoint] WARNING: no plugin found at $PLUGIN_STAGE"
fi

exec openclaw "$@"
