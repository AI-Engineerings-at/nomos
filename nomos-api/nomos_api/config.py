"""NomOS API configuration — Vault-first, then environment variables.

Priority: Vault > ENV > defaults.
Startup validation ensures no insecure defaults run in production.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Insecure defaults that MUST be overridden in production.
_INSECURE_DEFAULTS: dict[str, str] = {
    "jwt_secret": "change-me-in-production",
    "plugin_api_key": "nomos-plugin-dev",
    "gateway_token": "nomos-dev-token",
    "db_password": "nomos",
}


class Settings(BaseSettings):
    """API settings. Vault-first, then NOMOS_ prefixed env vars."""

    database_url: str = "postgresql+asyncpg://nomos:nomos@localhost:5432/nomos"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "NomOS Fleet API"
    api_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3040"]
    agents_dir: Path = Path("./data/agents")

    # Secrets — MUST be overridden via Vault or ENV
    jwt_secret: str = "change-me-in-production"
    plugin_api_key: str = "nomos-plugin-dev"
    gateway_url: str = "http://openclaw-gateway:18789"
    gateway_token: str = "nomos-dev-token"
    db_password: str = "nomos"

    # Vault connection
    vault_addr: str = "http://vault:8200"
    vault_role_id: str = ""
    vault_secret_id: str = ""

    # Runtime
    dev_mode: bool = False
    valkey_url: str = "redis://valkey:6379"
    retention_days: int = 365
    pii_filter_mode: str = "standard"

    model_config = {"env_prefix": "NOMOS_", "env_file": ".env", "extra": "ignore"}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        """Vault source is checked BEFORE env, so Vault secrets take priority."""
        from nomos_api.vault_source import VaultSettingsSource

        return (
            init_settings,
            VaultSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


def validate_settings(s: Settings) -> None:
    """Validate that no insecure defaults are active. Exits on violation.

    Skipped when dev_mode is True.
    """
    if s.dev_mode:
        logger.warning("DEV_MODE active — skipping secret validation. NOT for production!")
        return

    violations: list[str] = []
    for field, insecure_value in _INSECURE_DEFAULTS.items():
        actual = getattr(s, field, None)
        if actual == insecure_value:
            violations.append(field)

    if violations:
        logger.critical(
            "FATAL: Insecure default values detected for: %s. "
            "Set these via Vault or NOMOS_ environment variables, "
            "or set NOMOS_DEV_MODE=true for development.",
            ", ".join(violations),
        )
        sys.exit(1)


settings = Settings()
