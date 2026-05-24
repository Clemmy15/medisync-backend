"""API tests for DSN x Bluechip challenge agents."""

import pytest
from httpx import AsyncClient


async def _seed_profile(client: AsyncClient, headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/profile",
        headers=headers,
        json={
            "age_range": "18-24",
            "occupation": "University Student",
            "sleep_pattern": "5-6 hours",
            "stress_level": "high",
            "health_goals": "improve sleep",
            "activity_level": "low",
            "communication_style": "casual",
        },
    )


@pytest.mark.asyncio
async def test_cold_start_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agents/cold-start", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cold_start_output_shape(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    response = await client.post(
        "/api/v1/agents/cold-start",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"]
    assert len(data["recommendations"]) >= 1
    assert data["reasoning"]
    assert "steps" in data
    cats = {r["category"] for r in data["recommendations"]}
    assert len(cats) >= 1


@pytest.mark.asyncio
async def test_cross_domain_rank(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    response = await client.post(
        "/api/v1/agents/cross-domain/rank",
        headers=auth_headers,
        json={"concern": "Poor sleep and fatigue"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["concern"] == "Poor sleep and fatigue"
    assert len(data["ranked_recommendations"]) >= 1
    metrics = data["ranking_metrics"]
    assert "ndcg_at_10" in metrics
    assert "hit_rate" in metrics
    assert "recommendation_diversity" in metrics


@pytest.mark.asyncio
async def test_orchestrate_pipeline(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    response = await client.post(
        "/api/v1/agents/orchestrate",
        headers=auth_headers,
        json={"concern": "Poor sleep", "run_cold_start": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"]
    assert data["status"] == "completed"
    steps = {s["step"] for s in data["pipeline"]}
    assert "profile" in steps
    assert "memory" in steps


@pytest.mark.asyncio
async def test_explanation_after_orchestrate(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Wakes up tired after late study"},
    )
    await client.post("/api/v1/persona/generate", headers=auth_headers)
    orch = await client.post(
        "/api/v1/agents/orchestrate",
        headers=auth_headers,
        json={"concern": "Poor sleep"},
    )
    assert orch.status_code == 200
    explanation_id = orch.json().get("explanation_id")
    if explanation_id:
        exp = await client.get(
            f"/api/v1/explanations/{explanation_id}",
            headers=auth_headers,
        )
        assert exp.status_code == 200
        body = exp.json()
        assert body["reasoning"]
        assert "confidence_score" in body


@pytest.mark.asyncio
async def test_evaluation_task_a(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    await client.post("/api/v1/persona/generate", headers=auth_headers)
    sim = await client.post(
        "/api/v1/simulation/review",
        headers=auth_headers,
        json={
            "product_description": "Sleep tracking mobile app",
            "target_type": "healthcare_apps",
        },
    )
    assert sim.status_code == 200
    assert sim.json().get("fidelity") is not None

    report = await client.post(
        "/api/v1/evaluation/task-a",
        headers=auth_headers,
        json={"expected_rating": sim.json()["rating"]},
    )
    assert report.status_code == 200
    metrics = report.json()["metrics"]
    assert "rating_accuracy" in metrics
    assert "behavioural_fidelity" in metrics
    assert "review_quality_score" in metrics


@pytest.mark.asyncio
async def test_evaluation_task_b(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _seed_profile(client, auth_headers)
    rank = await client.post(
        "/api/v1/agents/cross-domain/rank",
        headers=auth_headers,
        json={"concern": "Poor sleep"},
    )
    batch_id = rank.json().get("batch_id")
    report = await client.post(
        "/api/v1/evaluation/task-b",
        headers=auth_headers,
        json={"batch_id": batch_id},
    )
    assert report.status_code == 200
    metrics = report.json()["metrics"]
    assert "ndcg_at_10" in metrics
    assert "contextual_relevance" in metrics
