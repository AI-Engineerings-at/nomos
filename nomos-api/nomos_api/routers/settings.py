"""System settings — read config from Vault, write via PATCH (admin-only)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.jwt import decode_token
from nomos_api.config import settings as app_settings
from nomos_api.database import get_db
from nomos_api.models import User
from nomos_api.schemas import SettingsUpdateRequest, SystemSettingsResponse
from nomos_api.vault_source import _get_vault_client

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {"openai_api_key", "anthropic_api_key", "nvidia_api_key"}

# Maps field names to Vault KV v2 paths and the key within that path.
_VAULT_CONFIG_MAP: dict[str, tuple[str, str]] = {
    "gateway_url": ("config/settings", "gateway_url"),
    "retention_days": ("config/settings", "retention_days"),
    "pii_filter_mode": ("config/settings", "pii_filter_mode"),
}
_VAULT_SECRET_MAP: dict[str, tuple[str, str]] = {
    "openai_api_key": ("secrets/llm_keys", "openai_api_key"),
    "anthropic_api_key": ("secrets/llm_keys", "anthropic_api_key"),
    "nvidia_api_key": ("secrets/llm_keys", "nvidia_api_key"),
}

router = APIRouter(prefix="/api/settings", tags=["settings"])


async def _require_admin(
    nomos_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: require admin role via JWT cookie."""
    if not nomos_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(nomos_token, app_settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(
        select(User).where(User.id == payload.user_id, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _vault_get_str(vault, path: str, key: str) -> str | None:
    """Read a single string value from a Vault KV v2 path."""
    data = vault.get_secret(path)
    if data and isinstance(data, dict) and key in data:
        return str(data[key])
    return None


def _read_current_settings(vault) -> SystemSettingsResponse:
    """Build SystemSettingsResponse from Vault (with app_settings fallback)."""
    return SystemSettingsResponse(
        gateway_url=(
            _vault_get_str(vault, "config/settings", "gateway_url")
            or app_settings.gateway_url
        ),
        retention_days=int(
            _vault_get_str(vault, "config/settings", "retention_days")
            or app_settings.retention_days
        ),
        pii_filter_mode=(
            _vault_get_str(vault, "config/settings", "pii_filter_mode")
            or app_settings.pii_filter_mode
        ),
        openai_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "openai_api_key") is not None,
        anthropic_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "anthropic_api_key") is not None,
        nvidia_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "nvidia_api_key") is not None,
    )


@router.get("", response_model=SystemSettingsResponse)
async def get_settings() -> SystemSettingsResponse:
    """Return current system settings. Config values in cleartext, secrets as booleans."""
    vault = _get_vault_client()
    return _read_current_settings(vault)


@router.patch("", response_model=SystemSettingsResponse)
async def update_settings(
    updates: SettingsUpdateRequest,
    _admin: User = Depends(_require_admin),
) -> SystemSettingsResponse:
    """Update system settings (admin-only). Writes config and secrets to Vault."""
    vault = _get_vault_client()
    if not vault.connected:
        raise HTTPException(status_code=503, detail="Vault unavailable — cannot persist settings")

    changed: list[str] = []
    fields = updates.model_dump(exclude_unset=True)

    # Collect config fields and write as a single KV entry to config/settings
    config_updates: dict[str, str] = {}
    for field_name in ("gateway_url", "retention_days", "pii_filter_mode"):
        if field_name in fields and fields[field_name] is not None:
            config_updates[field_name] = str(fields[field_name])
            changed.append(field_name)

    if config_updates:
        # Merge with existing config values
        existing_config = vault.get_secret("config/settings") or {}
        merged_config = {**existing_config, **config_updates}
        vault.put_secret("config/settings", merged_config)

    # Write LLM secrets individually to secrets/llm_keys
    secret_updates: dict[str, str] = {}
    for field_name in ("openai_api_key", "anthropic_api_key", "nvidia_api_key"):
        if field_name in fields and fields[field_name] is not None:
            secret_updates[field_name] = str(fields[field_name])
            changed.append(field_name)

    if secret_updates:
        existing_secrets = vault.get_secret("secrets/llm_keys") or {}
        merged_secrets = {**existing_secrets, **secret_updates}
        vault.put_secret("secrets/llm_keys", merged_secrets)

    logger.info(
        "Settings updated: %s",
        [k if k not in SENSITIVE_KEYS else f"{k}=***" for k in changed],
    )
    return _read_current_settings(vault)
