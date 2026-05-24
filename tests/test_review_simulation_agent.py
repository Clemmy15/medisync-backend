"""API tests for Review Simulation Agent."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_simulation_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/simulation/review",
        json={
            "persona_name": "Sleep Deprived Student",
            "product_description": "Sleep tracking app",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_review_simulation_output_shape(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "persona_name": "Sleep Deprived Student",
            "persona_reasoning": "University student with irregular sleep",
            "product_description": "A sleep tracking mobile app with smart alarms",
            "target_type": "healthcare_apps",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert 1 <= data["rating"] <= 5
    assert data["review"]
    assert data["reasoning"]
    assert data["target_type"] == "healthcare_apps"
    assert data["persona_name"] == "Sleep Deprived Student"
    assert "steps" in data
    assert "reasoning_trace" in data
    assert len(data["steps"]) >= 5
    assert data["steps"] == data["reasoning_trace"]["steps"]


@pytest.mark.asyncio
async def test_review_simulation_telemedicine_service(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "persona_name": "Busy Professional",
            "persona_reasoning": "High-stress office worker",
            "service_description": "24/7 telemedicine with video consultations",
            "target_type": "telemedicine_services",
        },
    )
    assert response.status_code == 200
    assert response.json()["target_type"] == "telemedicine_services"


@pytest.mark.asyncio
async def test_review_simulation_requires_description(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={"persona_name": "Test", "target_type": "pharmacies"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_review_simulation_history(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "persona_name": "Fitness Enthusiast",
            "persona_reasoning": "Active lifestyle",
            "product_description": "Protein supplement powder",
            "target_type": "wellness_products",
        },
    )
    history = await client.get("/api/v1/simulation/history", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) >= 1
