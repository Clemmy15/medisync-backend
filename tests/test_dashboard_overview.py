"""User dashboard overview endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_overview_returns_charts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={
            "age_range": "25-34",
            "occupation": "Engineer",
            "stress_level": "Moderate",
            "sleep_pattern": "6-7 hours",
        },
    )
    response = await client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "persona" in data
    assert "health_summary" in data
    assert "risk" in data
    assert "recommendation_count" in data
    assert "recent_activity" in data
    assert len(data["sleep_trend_chart"]["labels"]) == 14
    assert len(data["stress_trend_chart"]["datasets"][0]["data"]) == 14
    assert len(data["recommendation_activity_chart"]["labels"]) == 14
