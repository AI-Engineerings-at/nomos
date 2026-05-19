"""System status and unseal-key endpoints for the setup wizard.

GET /api/system/status — public, returns system initialization state.
GET /api/system/unseal-key — public, one-time unseal key retrieval.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.models import User
from nomos_api.schemas import SystemStatusResponse, UnsealKeyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])


def _get_served_marker_path() -> Path:
    """Durable one-shot marker for unseal-key retrieval.

    A filesystem marker (not an in-memory flag) so the one-time guarantee
    survives container restarts and is shared across uvicorn workers.
    Extracted for test patching.
    """
    return Path("/vault/init/unseal-key-served")


def _get_init_file_path() -> Path:
    """Return the path to the Vault init marker file.

    Extracted as a function to allow test patching without touching the filesystem.
    """
    return Path("/vault/init/initialized")


def _get_unseal_key_paths() -> list[Path]:
    """Return candidate paths for the unseal key, in priority order.

    First match wins. Extracted for test patching.
    """
    return [
        Path("/vault/init/unseal-key"),
        Path("/vault/file/init-output.json"),
    ]


def _get_vault_status() -> str:
    """Return Vault health status string."""
    from nomos_api.config import settings

    if not settings.vault_role_id or not settings.vault_secret_id:
        return "unavailable"

    try:
        from nomos_api.vault_source import _get_vault_client

        client = _get_vault_client()
        if not client.connected:
            return "unavailable"
        status = client.health_status()
        # Map 'degraded' to 'sealed' for the setup wizard context
        if status == "degraded":
            return "sealed"
        return status
    except Exception:
        return "unavailable"


async def _admin_exists(db: AsyncSession) -> bool:
    """Check if at least one admin user exists in the database."""
    result = await db.execute(select(func.count()).select_from(User).where(User.role == "admin"))
    count = result.scalar_one()
    return count > 0


def _read_unseal_key(paths: list[Path]) -> str | None:
    """Read the unseal key from the first existing candidate path.

    Supports two formats:
    - Plain text file (first path) — content is the key.
    - JSON file (init-output.json) — key is in unseal_keys_b64[0].
    """
    for path in paths:
        if not path.exists():
            continue

        content = path.read_text().strip()

        if path.name == "init-output.json":
            try:
                data = json.loads(content)
                keys = data.get("unseal_keys_b64", [])
                if keys:
                    return keys[0]
            except (json.JSONDecodeError, KeyError, IndexError):
                logger.warning("Failed to parse unseal key from %s", path)
                continue
        else:
            return content

    return None


@router.get("/status", response_model=SystemStatusResponse)
async def system_status(db: AsyncSession = Depends(get_db)) -> SystemStatusResponse:
    """Return system initialization status. Public endpoint, no auth required."""
    init_file = _get_init_file_path()
    initialized = init_file.exists()
    vault_status = _get_vault_status()
    admin = await _admin_exists(db)
    setup_required = not initialized or not admin

    return SystemStatusResponse(
        initialized=initialized,
        vault_status=vault_status,
        admin_exists=admin,
        setup_required=setup_required,
    )


@router.get("/unseal-key", response_model=UnsealKeyResponse)
async def get_unseal_key(db: AsyncSession = Depends(get_db)) -> UnsealKeyResponse:
    """Return the Vault unseal key — bootstrap-only, one-time retrieval.

    Two independent, restart-durable gates protect this public endpoint:

    1. Setup-complete gate: once any admin user exists, setup is finished
       and the unseal key is NEVER served again (403). This is derived from
       persistent DB state, so it survives restarts and worker recycling.
    2. One-shot gate: a filesystem marker is written on first successful
       retrieval; subsequent calls get 410. The marker (not an in-memory
       flag) holds across restarts and across uvicorn workers.

    - Setup already complete (admin exists): 403 Forbidden.
    - Already served: 410 Gone.
    - Key file not found: 404 Not Found.
    """
    if await _admin_exists(db):
        raise HTTPException(
            status_code=403,
            detail="Setup is complete; unseal key retrieval is permanently disabled",
        )

    marker = _get_served_marker_path()
    if marker.exists():
        raise HTTPException(status_code=410, detail="Unseal key has already been served")

    paths = _get_unseal_key_paths()
    key = _read_unseal_key(paths)

    if key is None:
        raise HTTPException(status_code=404, detail="Unseal key file not found")

    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("served")
    except OSError:
        logger.exception("Failed to persist unseal-key served marker at %s", marker)
        raise HTTPException(
            status_code=500,
            detail="Unable to record unseal-key retrieval; refusing to serve key",
        ) from None

    return UnsealKeyResponse(unseal_key=key)
