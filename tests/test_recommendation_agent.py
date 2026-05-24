"""API tests for Recommendation Agent."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_recommendation_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/recommendations/generate",
        json={},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_recommendation_output_shape(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={
            "age_range": "18-24",
            "occupation": "University Student",
            "sleep_pattern": "5-6 hours",
            "stress_level": "high",
            "health_goals": "improve sleep",
        },
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Studies late until 2am"},
    )
    await client.post("/api/v1/persona/generate", headers=auth_headers)

    response = await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "sleep_improvement"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["category"] == "sleep_improvement"
    assert len(data["recommendation"]) > 0
    assert len(data["reasoning"]) > 0
    assert 0.0 < data["confidence"] <= 1.0
    assert "steps" in data
    assert "reasoning_trace" in data
    steps = data["steps"]
    assert "Retrieved user profile" in steps
    assert "Retrieved user persona" in steps
    assert "Retrieved behavioural memory" in steps
    assert any("Reasoned" in s for s in steps)


@pytest.mark.asyncio
async def test_recommendation_history(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "stress_reduction"},
    )
    await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "hydration_improvement"},
    )

    history = await client.get(
        "/api/v1/recommendations/history",
        headers=auth_headers,
    )
    assert history.status_code == 200
    assert len(history.json()) >= 2

    filtered = await client.get(
        "/api/v1/recommendations/history?category=stress_reduction",
        headers=auth_headers,
    )
    assert all(r["category"] == "stress_reduction" for r in filtered.json())


@pytest.mark.asyncio
async def test_recommendation_current(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    gen = await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "health_apps"},
    )
    rec_text = gen.json()["recommendation"]

    current = await client.get(
        "/api/v1/recommendations/current",
        headers=auth_headers,
    )
    assert current.status_code == 200
    assert current.json()["recommendation"] == rec_text
