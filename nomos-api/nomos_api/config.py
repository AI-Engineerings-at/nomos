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
# Includes both legacy dev defaults and the Vault-pending sentinel.
_INSECURE_DEFAULTS: dict[str, set[str]] = {
    "jwt_secret": {"change-me-in-production", "vault-pending"},
    "plugin_api_key": {"nomos-plugin-dev", "vault-pending"},
    "gateway_token": {"nomos-dev-token", "vault-pending"},
    "db_password": {"nomos", "vault-pending"},
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

    # Secrets — overridden via Vault (auto) or ENV.
    # "vault-pending" means Vault has not yet injected the real value.
    # validate_settings() blocks this in production.
    jwt_secret: str = "vault-pending"
    plugin_api_key: str = "vault-pending"
    gateway_url: str = "http://openclaw-gateway:18789"
    gateway_token: str = "vault-pending"
    db_password: str = "vault-pending"

    # Vault connection
    vault_addr: str = "http://vault:8200"
    vault_role_id: str = ""
    vault_secret_id: str = ""

    # LLM Provider (direct passthrough, bypasses OpenClaw agent loop)
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    # Runtime
    dev_mode: bool = False
    cookie_secure: bool = True
    valkey_url: str = "valkey://valkey:6379"
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
    for field, insecure_values in _INSECURE_DEFAULTS.items():
        actual = getattr(s, field, None)
        if actual in insecure_values:
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
validate_settings(settings)
