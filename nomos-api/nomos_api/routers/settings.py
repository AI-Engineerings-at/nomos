"""System settings endpoint — read-only configuration for the console."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from nomos_api.config import settings as app_settings


class SystemSettingsResponse(BaseModel):
    gateway_url: str
    retention_days: int
    pii_filter_mode: str  # "strict" | "standard" | "off"


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsResponse)
async def get_settings() -> SystemSettingsResponse:
    """Return current system settings (read-only)."""
    return SystemSettingsResponse(
        gateway_url=app_settings.gateway_url,
        retention_days=app_settings.retention_days,
        pii_filter_mode=app_settings.pii_filter_mode,
    )
