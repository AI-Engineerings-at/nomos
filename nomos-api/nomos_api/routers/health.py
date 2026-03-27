"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from nomos_api.config import settings
from nomos_api.schemas import HealthResponse

router = APIRouter(tags=["health"])


def _get_vault_status() -> str:
    """Return Vault health status string for the health endpoint."""
    if not settings.vault_role_id or not settings.vault_secret_id:
        return "not_configured"

    try:
        from nomos_api.vault_source import _get_vault_client

        client = _get_vault_client()
        if not client.connected:
            return "unavailable"
        return client.health_status()
    except Exception:
        return "unavailable"


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse, include_in_schema=False)
async def health() -> HealthResponse:
    vault_status = _get_vault_status()
    return HealthResponse(
        status="healthy",
        service=settings.api_title,
        version=settings.api_version,
        vault=vault_status,
    )
