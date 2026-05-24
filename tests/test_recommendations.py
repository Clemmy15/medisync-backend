"""Legacy recommendation test — delegates to full agent suite."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_recommendation(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendation" in data
    assert "reasoning" in data
    assert "confidence" in data
    assert "category" in data
    assert "steps" in data
    assert "reasoning_trace" in data
