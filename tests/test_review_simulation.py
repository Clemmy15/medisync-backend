"""Legacy review simulation test."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_simulation(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "persona_name": "Sleep Deprived Student",
            "persona_reasoning": "Student with poor sleep habits",
            "product_description": "A sleep tracking mobile app with smart alarms",
            "target_type": "healthcare_apps",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert 1 <= data["rating"] <= 5
    assert data["review"]
    assert data["reasoning"]
    assert "steps" in data
    assert "reasoning_trace" in data
