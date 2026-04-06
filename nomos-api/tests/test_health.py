"""Tests for health endpoint."""

from __future__ import annotations


class TestHealth:
    async def test_health_returns_ok(self, client) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["service"] == "NomOS Fleet API"
        assert "version" in data

    async def test_health_contains_components(self, client) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()

        components = data.get("components")
        assert components is not None, "components field must be present"

        for key in ("vault", "postgres", "valkey", "gateway"):
            assert key in components, f"components.{key} must be present"
            assert isinstance(components[key], str), f"components.{key} must be a string"

    async def test_health_uptime_seconds(self, client) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()

        uptime = data.get("uptime_seconds")
        assert uptime is not None, "uptime_seconds field must be present"
        assert isinstance(uptime, int)
        assert uptime >= 0

    async def test_health_vault_field_present(self, client) -> None:
        """Backwards-compat: top-level vault field is still returned."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "vault" in data
        assert isinstance(data["vault"], str)
