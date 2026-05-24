"""API tests for User Persona Engine."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_persona_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/persona/generate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_persona_output_shape(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={
            "age_range": "18-24",
            "occupation": "University Student",
            "stress_level": "high",
            "sleep_pattern": "5-6 hours",
            "health_goals": "improve sleep",
        },
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Studies late until 2am before exams"},
    )

    response = await client.post(
        "/api/v1/persona/generate",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "persona_name" in data
    assert "reasoning" in data
    assert "confidence_score" in data
    assert "steps" in data
    assert "reasoning_trace" in data
    assert data["steps"] == data["reasoning_trace"]["steps"]
    assert len(data["persona_name"]) > 0
    assert len(data["reasoning"]) > 0
    assert 0.0 < data["confidence_score"] <= 1.0


@pytest.mark.asyncio
async def test_persona_history(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/persona/generate", headers=auth_headers)
    await client.post("/api/v1/persona/generate", headers=auth_headers)

    history = await client.get("/api/v1/persona/history", headers=auth_headers)
    assert history.status_code == 200
    items = history.json()
    assert len(items) >= 2
    assert items[0]["persona_name"]
    assert items[0]["reasoning"]
    assert "sources_used" in items[0]


@pytest.mark.asyncio
async def test_persona_current(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    gen = await client.post("/api/v1/persona/generate", headers=auth_headers)
    generated_name = gen.json()["persona_name"]

    current = await client.get("/api/v1/persona/current", headers=auth_headers)
    assert current.status_code == 200
    assert current.json()["persona_name"] == generated_name


@pytest.mark.asyncio
async def test_persona_current_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    # Fresh user from auth_headers fixture may already have persona from other tests
    # Register a new user instead
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Persona New",
            "email": "persona_new@test.com",
            "password": "testpass123",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "persona_new@test.com", "password": "testpass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get("/api/v1/persona/current", headers=headers)
    assert response.status_code == 404
