"""System settings — read config from Vault, write via PATCH (admin-only)."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

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

# gateway_url is an SSRF-relevant outbound target. Only http/https are
# acceptable; schemes like file://, gopher://, ftp://, unix:// etc. are
# rejected to prevent a PATCH from pivoting requests to internal resources.
_ALLOWED_URL_SCHEMES = {"http", "https"}


def _validate_gateway_url(value: str) -> str:
    """Validate a gateway URL. Raises HTTP 422 on an unsafe/invalid value."""
    parsed = urlparse(value)
    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
        raise HTTPException(
            status_code=422,
            detail="gateway_url must use http or https scheme",
        )
    if not parsed.netloc:
        raise HTTPException(
            status_code=422,
            detail="gateway_url must include a host",
        )
    return value


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


async def _require_user(
    nomos_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: require any authenticated, active user via JWT cookie.

    GET /api/settings previously had NO route-level auth (H4). It is now
    gated to authenticated users; cleartext gateway_url is further
    restricted to admins (see get_settings).
    """
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
        gateway_url=(_vault_get_str(vault, "config/settings", "gateway_url") or app_settings.gateway_url),
        retention_days=int(_vault_get_str(vault, "config/settings", "retention_days") or app_settings.retention_days),
        pii_filter_mode=(_vault_get_str(vault, "config/settings", "pii_filter_mode") or app_settings.pii_filter_mode),
        openai_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "openai_api_key") is not None,
        anthropic_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "anthropic_api_key") is not None,
        nvidia_api_key_set=_vault_get_str(vault, "secrets/llm_keys", "nvidia_api_key") is not None,
    )


@router.get("", response_model=SystemSettingsResponse)
async def get_settings(
    user: User = Depends(_require_user),
) -> SystemSettingsResponse:
    """Return current system settings.

    Requires authentication (H4). Secrets are exposed only as booleans. The
    SSRF-relevant cleartext ``gateway_url`` is admin-only; non-admin users
    (who need the provider-configured banner on the chat page) receive a
    a redacted value instead of the real internal URL.
    """
    vault = _get_vault_client()
    resp = _read_current_settings(vault)
    if user.role != "admin":
        resp.gateway_url = "***"
    return resp


@router.patch("", response_model=SystemSettingsResponse)
async def update_settings(
    updates: SettingsUpdateRequest,
    _admin: User = Depends(_require_admin),
) -> SystemSettingsResponse:
    """Update system settings (admin-only). Writes config and secrets to Vault."""
    changed: list[str] = []
    fields = updates.model_dump(exclude_unset=True)

    # SSRF guard: validate gateway_url BEFORE any persistence or Vault access,
    # so an unsafe scheme is rejected (422) regardless of Vault availability.
    if fields.get("gateway_url") is not None:
        _validate_gateway_url(str(fields["gateway_url"]))

    vault = _get_vault_client()
    if not vault.connected:
        raise HTTPException(status_code=503, detail="Vault unavailable — cannot persist settings")

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
