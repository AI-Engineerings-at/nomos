"""Health check endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter
from sqlalchemy import text

from nomos_api.config import settings
from nomos_api.schemas import HealthComponentStatus, HealthResponse

router = APIRouter(tags=["health"])

_start_time = time.time()


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


async def _check_postgres() -> str:
    """Verify PostgreSQL connectivity with a lightweight SELECT 1."""
    try:
        from nomos_api.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        return "unavailable"


async def _check_valkey() -> str:
    """Ping the Valkey instance and close the connection immediately."""
    try:
        import valkey.asyncio as valkey_client

        client = valkey_client.from_url(settings.valkey_url)
        await client.ping()
        await client.aclose()
        return "healthy"
    except Exception:
        return "unavailable"


async def _check_gateway() -> str:
    """GET the gateway /healthz endpoint; treat HTTP 200 as online."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.gateway_url}/healthz")
        return "online" if resp.status_code == 200 else "offline"
    except Exception:
        return "offline"


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse, include_in_schema=False)
async def health() -> HealthResponse:
    vault_status = _get_vault_status()
    pg = await _check_postgres()
    vk = await _check_valkey()
    gw = await _check_gateway()

    overall = "healthy" if pg == "healthy" else "degraded"

    return HealthResponse(
        status=overall,
        service=settings.api_title,
        version=settings.api_version,
        vault=vault_status,
        components=HealthComponentStatus(
            vault=vault_status,
            postgres=pg,
            valkey=vk,
            gateway=gw,
        ),
        uptime_seconds=int(time.time() - _start_time),
    )
