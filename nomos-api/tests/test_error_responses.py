"""Tests for standardized error responses with {detail, code, request_id}."""

from __future__ import annotations

from nomos_api.errors import ERROR_CODES, NomOSErrorResponse


class TestNomOSErrorResponseModel:
    def test_model_fields(self) -> None:
        """NomOSErrorResponse must have detail, code, and request_id fields."""
        resp = NomOSErrorResponse(detail="Not found", code="NOT_FOUND", request_id="req-123")
        assert resp.detail == "Not found"
        assert resp.code == "NOT_FOUND"
        assert resp.request_id == "req-123"

    def test_model_dump_structure(self) -> None:
        """model_dump() must produce a dict with exactly the expected keys."""
        resp = NomOSErrorResponse(detail="Error", code="BAD_REQUEST", request_id="req-456")
        data = resp.model_dump()
        assert set(data.keys()) == {"detail", "code", "request_id"}

    def test_error_codes_mapping(self) -> None:
        """ERROR_CODES must map standard HTTP status codes to string error codes."""
        assert ERROR_CODES[400] == "BAD_REQUEST"
        assert ERROR_CODES[401] == "AUTH_REQUIRED"
        assert ERROR_CODES[403] == "FORBIDDEN"
        assert ERROR_CODES[404] == "NOT_FOUND"
        assert ERROR_CODES[409] == "CONFLICT"
        assert ERROR_CODES[422] == "VALIDATION_ERROR"
        assert ERROR_CODES[429] == "RATE_LIMITED"
        assert ERROR_CODES[500] == "INTERNAL_ERROR"
        assert ERROR_CODES[502] == "GATEWAY_ERROR"
        assert ERROR_CODES[503] == "SERVICE_UNAVAILABLE"


class TestHTTPExceptionHandler:
    async def test_404_has_standard_format(self, client) -> None:
        """A 404 from HTTPException must return {detail, code, request_id}."""
        resp = await client.get("/api/fleet/nonexistent-agent-id")
        assert resp.status_code == 404
        data = resp.json()
        assert data["code"] == "NOT_FOUND"
        assert "detail" in data
        assert "request_id" in data
        # request_id must match the header
        assert data["request_id"] == resp.headers["X-Request-ID"]

    async def test_404_with_client_request_id(self, client) -> None:
        """Client-provided X-Request-ID must appear in the error response body."""
        custom_id = "error-trace-001"
        resp = await client.get(
            "/api/fleet/nonexistent-agent-id",
            headers={"X-Request-ID": custom_id},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert data["request_id"] == custom_id
        assert data["code"] == "NOT_FOUND"


class TestGeneralExceptionHandler:
    async def test_unhandled_exception_returns_500_with_format(self, client) -> None:
        """Unhandled exceptions must return standardized 500 with request_id."""
        from nomos_api.main import app

        # Add a temporary route that always raises an unhandled exception
        @app.get("/_test/explode")
        async def exploding_endpoint() -> None:
            raise RuntimeError("kaboom")

        try:
            resp = await client.get("/_test/explode")
            assert resp.status_code == 500
            data = resp.json()
            assert data["code"] == "INTERNAL_ERROR"
            assert data["detail"] == "Internal server error"
            assert "request_id" in data
            assert data["request_id"] == resp.headers["X-Request-ID"]
        finally:
            # Clean up the temporary route
            app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test/explode"]
