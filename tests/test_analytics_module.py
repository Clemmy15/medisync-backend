"""Tests for Analytics module."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import update

from app.models.user import User
from tests.conftest import TestSessionLocal

SAMPLE_CONTEXT = """
Symptoms: headaches. Sleep: 5-6 hours. Goals: improve sleep.
Habits: irregular schedule. Stress: work deadlines.
"""


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin User",
            "email": "admin-analytics@test.com",
            "password": "adminpass123",
        },
    )
    async with TestSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.email == "admin-analytics@test.com")
            .values(is_admin=True)
        )
        await session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-analytics@test.com", "password": "adminpass123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_analytics_overview_requires_admin(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analytics_overview_shape(
    client: AsyncClient, admin_headers: dict[str, str], auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/persona/generate", headers=auth_headers)
    await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "sleep_improvement"},
    )
    await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "persona_reasoning": "University student with irregular sleep",
            "product_description": "Sleep tracking app",
            "target_type": "healthcare_apps",
        },
    )
    await client.post(
        "/api/v1/context-import/save",
        headers=auth_headers,
        json={"content": SAMPLE_CONTEXT, "source_platform": "chatgpt"},
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Tracks sleep daily"},
    )

    response = await client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    assert metrics["total_users"] >= 2
    assert metrics["recommendations_generated"] >= 1
    assert metrics["reviews_simulated"] >= 1
    assert metrics["contexts_imported"] >= 1
    assert metrics["personas_generated"] >= 1
    assert metrics["total_memories"] >= 1

    assert len(data["activity_chart"]["labels"]) == 14
    assert len(data["activity_chart"]["datasets"]) == 3
    assert len(data["memory_growth_chart"]["datasets"]) == 2


@pytest.mark.asyncio
async def test_analytics_personas_chart(
    client: AsyncClient, admin_headers: dict[str, str], auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/persona/generate", headers=auth_headers)

    response = await client.get("/api/v1/analytics/personas", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_personas"] >= 1
    assert len(data["distribution"]) >= 1
    assert data["chart"]["labels"]
    assert data["chart"]["datasets"][0]["data"]


@pytest.mark.asyncio
async def test_analytics_recommendations_chart(
    client: AsyncClient, admin_headers: dict[str, str], auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "stress_reduction"},
    )

    response = await client.get(
        "/api/v1/analytics/recommendations", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert 0.0 <= data["average_confidence"] <= 1.0
    assert len(data["by_category"]) >= 1
    assert data["category_chart"]["labels"]
    assert len(data["daily_chart"]["labels"]) == 14
