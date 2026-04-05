import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_budget_check_unknown_agent_returns_restrictive(client: AsyncClient):
    """Unknown agents get fail-closed response, not 404."""
    response = await client.post("/api/budget/check", json={
        "agent_id": "nonexistent-agent",
        "estimated_cost": 0.01,
    })
    assert response.status_code == 200  # Not 404
    data = response.json()
    assert data["allowed"] is False
    assert data["status"] == "unknown_agent"
    assert "reason" in data
