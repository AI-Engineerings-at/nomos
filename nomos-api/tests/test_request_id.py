"""Tests for X-Request-ID correlation middleware."""

from __future__ import annotations

import uuid


class TestRequestID:
    async def test_response_has_request_id_header(self, client) -> None:
        """Every response must include X-Request-ID, even if client didn't send one."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers

    async def test_client_request_id_echoed(self, client) -> None:
        """When client sends X-Request-ID, the server echoes it back unchanged."""
        custom_id = "my-custom-correlation-id-42"
        resp = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.headers["X-Request-ID"] == custom_id

    async def test_generated_id_is_valid_uuid(self, client) -> None:
        """Auto-generated request IDs must be valid UUID4 strings."""
        resp = await client.get("/health")
        request_id = resp.headers.get("X-Request-ID", "")
        # Must parse as a valid UUID
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    async def test_request_id_on_error_responses(self, client) -> None:
        """X-Request-ID must be present even on error responses (e.g. 404)."""
        resp = await client.get("/api/fleet/nonexistent-agent-id")
        assert resp.status_code == 404
        assert "X-Request-ID" in resp.headers

    async def test_different_requests_get_different_ids(self, client) -> None:
        """Two requests without X-Request-ID should get distinct generated IDs."""
        resp1 = await client.get("/health")
        resp2 = await client.get("/health")
        id1 = resp1.headers.get("X-Request-ID")
        id2 = resp2.headers.get("X-Request-ID")
        assert id1 != id2
