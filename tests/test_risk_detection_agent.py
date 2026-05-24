"""API tests for Risk Detection Agent."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_risk_detection_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/analysis/risk",
        json={"symptoms": ["headache", "fatigue"]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_risk_detection_output_shape(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Recurring headaches and poor sleep"},
    )
    response = await client.post(
        "/api/v1/analysis/risk",
        headers=auth_headers,
        json={
            "symptoms": ["persistent headache", "fatigue"],
            "context": "Symptoms worsening over two weeks",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("low", "moderate", "high")
    assert data["reasoning"]
    assert data["recommended_action"]
    assert "steps" in data
    assert len(data["steps"]) >= 6
    assert "dangerous symptom" in " ".join(data["steps"]).lower()
    assert "behavioural deterioration" in " ".join(data["steps"]).lower()
    assert "recurring health" in " ".join(data["steps"]).lower()


@pytest.mark.asyncio
async def test_risk_detection_history_and_current(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/analysis/risk",
        headers=auth_headers,
        json={"symptoms": ["dizziness"]},
    )

    current = await client.get(
        "/api/v1/analysis/risk/current", headers=auth_headers
    )
    assert current.status_code == 200
    assert current.json()["risk_level"] in ("low", "moderate", "high")

    history = await client.get(
        "/api/v1/analysis/risk/history", headers=auth_headers
    )
    assert history.status_code == 200
    assert len(history.json()) >= 1


@pytest.mark.asyncio
async def test_risk_current_not_found(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Risk Only",
            "email": "riskonly@example.com",
            "password": "testpass123",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "riskonly@example.com", "password": "testpass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.get("/api/v1/analysis/risk/current", headers=headers)
    assert response.status_code == 404
