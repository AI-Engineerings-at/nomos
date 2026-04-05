import pytest
from httpx import AsyncClient
from nomos_api.config import settings

@pytest.mark.asyncio
async def test_settings_patch_requires_admin(client: AsyncClient):
    """Non-admin cannot update settings."""
    # Note: client fixture in conftest.py uses a service key which acts as service, not admin
    # So this should fail with 401/403 if it expects a user session
    response = await client.patch("/api/settings", json={"retention_days": 30})
    # Since the client uses X-NomOS-API-Key which maps to role=service
    # And settings router uses _require_admin which checks nomos_token cookie
    assert response.status_code == 401 # No cookie

@pytest.mark.asyncio
async def test_get_settings_works(client: AsyncClient):
    """GET /api/settings returns settings."""
    # GET doesn't require admin in the current implementation of settings.py
    response = await client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "retention_days" in data
    assert "openai_api_key_set" in data
