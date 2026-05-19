"""L2 regression: security headers are present on responses."""

from __future__ import annotations


async def test_security_headers_present_on_public_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    csp = resp.headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


async def test_security_headers_present_on_auth_rejection(client, monkeypatch):
    """Headers must also be set on 401 (outermost middleware)."""
    from nomos_api.config import settings

    # A protected endpoint without proper auth -> 401, still gets headers.
    monkeypatch.setattr(settings, "plugin_api_key", "x" * 40)
    resp = await client.get("/api/settings", headers={"X-NomOS-API-Key": "wrong"})
    assert resp.status_code == 401
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


async def test_hsts_only_when_cookie_secure(client, monkeypatch):
    from nomos_api.config import settings

    monkeypatch.setattr(settings, "cookie_secure", True)
    resp = await client.get("/api/health")
    assert "Strict-Transport-Security" in resp.headers
    assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]


async def test_no_hsts_when_not_secure(client, monkeypatch):
    from nomos_api.config import settings

    monkeypatch.setattr(settings, "cookie_secure", False)
    resp = await client.get("/api/health")
    assert "Strict-Transport-Security" not in resp.headers
