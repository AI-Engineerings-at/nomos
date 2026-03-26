"""Tests for GET /api/settings endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_settings_returns_expected_fields(client: AsyncClient) -> None:
    """GET /api/settings returns gateway_url, retention_days, pii_filter_mode."""
    resp = await client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "gateway_url" in data
    assert "retention_days" in data
    assert "pii_filter_mode" in data


@pytest.mark.anyio
async def test_get_settings_default_values(client: AsyncClient) -> None:
    """Default values are sensible."""
    resp = await client.get("/api/settings")
    data = resp.json()
    assert isinstance(data["gateway_url"], str)
    assert isinstance(data["retention_days"], int)
    assert data["retention_days"] > 0
    assert data["pii_filter_mode"] in ("strict", "standard", "off")
