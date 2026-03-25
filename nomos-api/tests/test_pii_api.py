"""Tests for PII filter API endpoint."""

from __future__ import annotations


class TestPIIFilterEndpoint:
    async def test_filter_pii_email(self, client) -> None:
        response = await client.post("/api/pii/filter", json={
            "text": "Email: max@example.com, Tel: +43 1 234 5678"
        })
        assert response.status_code == 200
        data = response.json()
        assert "[EMAIL_REDACTED]" in data["filtered"]
        assert data["pii_count"] >= 1

    async def test_filter_clean_text(self, client) -> None:
        response = await client.post("/api/pii/filter", json={
            "text": "Keine PII hier"
        })
        data = response.json()
        assert data["pii_count"] == 0
        assert data["filtered"] == "Keine PII hier"

    async def test_filter_returns_matches(self, client) -> None:
        response = await client.post("/api/pii/filter", json={
            "text": "max@test.com ist erreichbar"
        })
        data = response.json()
        assert len(data["matches"]) == 1
        assert data["matches"][0]["type"] == "email"

    async def test_filter_empty_text_rejected(self, client) -> None:
        response = await client.post("/api/pii/filter", json={
            "text": ""
        })
        assert response.status_code == 422
