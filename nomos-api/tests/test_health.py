"""Tests for health endpoint."""

from __future__ import annotations

import pytest


class TestHealth:
    async def test_health_returns_ok(self, client) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "NomOS Fleet API"
        assert "version" in data
