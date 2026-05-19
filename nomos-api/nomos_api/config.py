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

# Clearly-invalid sentinel for database_url. Fails closed: it contains no
# working credentials, so an unconfigured deployment cannot silently connect
# with a known cleartext password.
_DATABASE_URL_PLACEHOLDER = "postgresql+asyncpg://CONFIGURE_NOMOS_DATABASE_URL@invalid-host:5432/nomos"

# Security-critical secrets that MUST always be real and strong, even when
# dev_mode is on. A short or sentinel value here is never acceptable because
# it gates authentication (jwt_secret signs the session cookie; plugin_api_key
# is the service-to-service bearer for the plugin).
_ALWAYS_REQUIRED_SECRETS: tuple[str, ...] = ("jwt_secret", "plugin_api_key")
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """API settings. Vault-first, then NOMOS_ prefixed env vars."""

    database_url: str = _DATABASE_URL_PLACEHOLDER
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


def _validate_always_required_secrets(s: Settings) -> list[str]:
    """Validate security-critical secrets that apply even in dev_mode.

    jwt_secret and plugin_api_key gate authentication, so an empty value, a
    known insecure default / "vault-pending" sentinel, or a too-short value is
    NEVER acceptable — not even in dev_mode. Returns a list of human-readable
    violation strings (empty == OK).
    """
    violations: list[str] = []
    for field in _ALWAYS_REQUIRED_SECRETS:
        actual = getattr(s, field, None)
        if not actual or not isinstance(actual, str):
            violations.append(f"{field} (empty — must be set)")
            continue
        if actual in _INSECURE_DEFAULTS.get(field, set()):
            violations.append(f"{field} (insecure default / vault-pending)")
            continue
        if len(actual) < _MIN_SECRET_LENGTH:
            violations.append(f"{field} (too short — needs >= {_MIN_SECRET_LENGTH} chars, got {len(actual)})")
    return violations


def validate_settings(s: Settings) -> None:
    """Validate that no insecure defaults are active. Exits on violation.

    Security-critical secrets (jwt_secret, plugin_api_key) are ALWAYS validated,
    even when dev_mode is True. dev_mode only relaxes non-security conveniences
    (e.g. gateway_token / db_password sentinels, extra CORS origins).
    """
    # Hard gate: always-required secrets are checked unconditionally.
    critical = _validate_always_required_secrets(s)
    if critical:
        logger.critical(
            "FATAL: Security-critical secrets are invalid even for dev_mode: %s. "
            "Set NOMOS_JWT_SECRET and NOMOS_PLUGIN_API_KEY to real values "
            "(>= %d chars) via Vault or environment variables.",
            ", ".join(critical),
            _MIN_SECRET_LENGTH,
        )
        sys.exit(1)

    if s.dev_mode:
        logger.warning(
            "DEV_MODE active — relaxing non-security secret validation "
            "(gateway_token/db_password). jwt_secret/plugin_api_key still enforced. "
            "NOT for production!"
        )
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
        if s.vault_addr and not s.vault_role_id:
            logger.critical(
                "Vault is configured but AppRole credentials are missing. "
                "Check vault-init container or VAULT_ROLE_ID/VAULT_SECRET_ID environment variables."
            )
        sys.exit(1)

    # Additional validation for production readiness
    if not s.dev_mode:
        logger.info("Production mode: All secret validations passed")
        if s.vault_addr:
            logger.info("Vault integration enabled at %s", s.vault_addr)


settings = Settings()
validate_settings(settings)
