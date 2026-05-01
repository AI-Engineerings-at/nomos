"""Pydantic Settings source backed by HashiCorp Vault.

Reads secrets from Vault KV v2 and injects them into Settings fields.
Lazy-imports VaultClient to avoid circular dependencies.

AppRole credentials are read from the shared init volume first
(/vault/init/approle-creds.env, written by vault-init container),
then fall back to VAULT_ROLE_ID / VAULT_SECRET_ID environment variables.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Default path where vault-init writes AppRole credentials.
APPROLE_CREDS_PATH: str = "/vault/init/approle-creds.env"

# Maps Settings field names to Vault KV v2 paths and keys.
# Paths match vault/init-entrypoint.sh:
#   vault kv put nomos/secrets/system jwt_secret=... plugin_api_key=... gateway_token=...
#   vault kv put nomos/secrets/database password=...
VAULT_FIELD_MAP: dict[str, tuple[str, str]] = {
    "jwt_secret": ("secrets/system", "jwt_secret"),
    "plugin_api_key": ("secrets/system", "plugin_api_key"),
    "gateway_token": ("secrets/system", "gateway_token"),
    "db_password": ("secrets/database", "password"),
    "llm_api_key": ("secrets/llm_keys", "nvidia_api_key"),
}

_vault_client_instance = None


def _read_creds_from_file(path: str = APPROLE_CREDS_PATH) -> tuple[str, str]:
    """Read VAULT_ROLE_ID and VAULT_SECRET_ID from init output file.

    Returns (role_id, secret_id). Both empty strings if file not found.
    """
    try:
        with open(path) as f:
            creds: dict[str, str] = {}
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    creds[key.strip()] = val.strip()
            role_id = creds.get("VAULT_ROLE_ID", "")
            secret_id = creds.get("VAULT_SECRET_ID", "")
            if role_id and secret_id:
                logger.debug("Successfully read AppRole credentials from %s", path)
            return role_id, secret_id
    except FileNotFoundError:
        logger.debug("AppRole credentials file not found at %s", path)
        return "", ""
    except Exception as exc:
        logger.error("Failed to read AppRole credentials from %s: %s", path, exc)
        return "", ""


def _get_vault_client():
    """Singleton factory for VaultClient. Lazy import to avoid circular deps.

    Reads AppRole credentials from shared volume first, then ENV fallback.
    """
    global _vault_client_instance
    if _vault_client_instance is None:
        from nomos_api.vault_client import VaultClient

        # Try file first (written by vault-init container)
        role_id, secret_id = _read_creds_from_file(APPROLE_CREDS_PATH)

        if role_id and secret_id:
            logger.info("AppRole credentials loaded from %s", APPROLE_CREDS_PATH)
        else:
            # Fallback to environment variables
            role_id = os.environ.get("VAULT_ROLE_ID", "")
            secret_id = os.environ.get("VAULT_SECRET_ID", "")
            if role_id and secret_id:
                logger.info("AppRole credentials loaded from environment variables")

        _vault_client_instance = VaultClient(
            addr=os.environ.get("VAULT_ADDR", "http://vault:8200"),
            role_id=role_id,
            secret_id=secret_id,
        )
    return _vault_client_instance


class VaultSettingsSource:
    """Custom pydantic-settings source that reads from Vault."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        self.settings_cls = settings_cls

    def __call__(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        client = _get_vault_client()

        if not client.connected:
            logger.warning("Vault not connected, skipping Vault settings source")
            return values

        # Group by vault path to minimize reads
        paths_seen: dict[str, dict[str, Any] | None] = {}

        for field_name, (vault_path, vault_key) in VAULT_FIELD_MAP.items():
            if vault_path not in paths_seen:
                secret_data = client.get_secret(vault_path)
                paths_seen[vault_path] = secret_data
                if secret_data is None:
                    logger.warning("No secret data found at Vault path %s", vault_path)

            secret_data = paths_seen[vault_path]
            if secret_data and vault_key in secret_data:
                values[field_name] = secret_data[vault_key]
                logger.info("Loaded %s from Vault path %s", field_name, vault_path)
            else:
                logger.debug("Field %s not found in Vault path %s", vault_key, vault_path)

        if not values:
            logger.warning("No settings loaded from Vault - check Vault initialization and policies")

        return values
