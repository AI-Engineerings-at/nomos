"""Pydantic Settings source backed by HashiCorp Vault.

Reads secrets from Vault KV v2 and injects them into Settings fields.
Lazy-imports VaultClient to avoid circular dependencies.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Maps Settings field names to Vault KV v2 paths and keys.
# Example: jwt_secret -> read nomos/data/api/secrets, take key "jwt_secret"
VAULT_FIELD_MAP: dict[str, tuple[str, str]] = {
    "jwt_secret": ("api/secrets", "jwt_secret"),
    "plugin_api_key": ("api/secrets", "plugin_api_key"),
    "gateway_token": ("api/secrets", "gateway_token"),
    "db_password": ("db/credentials", "password"),
}

_vault_client_instance = None


def _get_vault_client():
    """Singleton factory for VaultClient. Lazy import to avoid circular deps."""
    global _vault_client_instance
    if _vault_client_instance is None:
        from nomos_api.vault_client import VaultClient

        _vault_client_instance = VaultClient(
            addr=os.environ.get("VAULT_ADDR", "http://vault:8200"),
            role_id=os.environ.get("VAULT_ROLE_ID", ""),
            secret_id=os.environ.get("VAULT_SECRET_ID", ""),
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
            return values

        # Group by vault path to minimize reads
        paths_seen: dict[str, dict[str, Any] | None] = {}

        for field_name, (vault_path, vault_key) in VAULT_FIELD_MAP.items():
            if vault_path not in paths_seen:
                paths_seen[vault_path] = client.get_secret(vault_path)

            secret_data = paths_seen[vault_path]
            if secret_data and vault_key in secret_data:
                values[field_name] = secret_data[vault_key]
                logger.debug("Loaded %s from Vault path %s", field_name, vault_path)

        return values
