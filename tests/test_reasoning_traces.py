"""Tests for transparent reasoning traces across agents."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_persona_response_includes_steps(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/persona/generate", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) >= 4
    assert data["steps"] == data["reasoning_trace"]["steps"]
    assert "Retrieved user profile" in data["steps"]


@pytest.mark.asyncio
async def test_reasoning_traces_api_after_persona(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/persona/generate", headers=auth_headers)

    listing = await client.get("/api/v1/reasoning/traces", headers=auth_headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] >= 1
    assert len(body["traces"]) >= 1
    trace = body["traces"][0]
    assert trace["trace_type"] == "persona"
    assert len(trace["steps"]) >= 4

    latest = await client.get(
        "/api/v1/reasoning/traces/latest",
        headers=auth_headers,
        params={"trace_type": "persona"},
    )
    assert latest.status_code == 200
    assert latest.json()["trace_type"] == "persona"

    by_id = await client.get(
        f"/api/v1/reasoning/traces/{trace['id']}",
        headers=auth_headers,
    )
    assert by_id.status_code == 200
    assert by_id.json()["steps"] == trace["steps"]


@pytest.mark.asyncio
async def test_recommendation_steps(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post("/api/v1/persona/generate", headers=auth_headers)
    response = await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={"category": "sleep_improvement"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Matched recommendation" in " ".join(data["steps"])


@pytest.mark.asyncio
async def test_memory_search_steps(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "User reports poor sleep quality"},
    )
    response = await client.post(
        "/api/v1/memory/search",
        headers=auth_headers,
        json={"query": "sleep problems"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert "semantic vector search" in " ".join(data["steps"]).lower()


@pytest.mark.asyncio
async def test_context_analyze_steps(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/context-import/analyze",
        headers=auth_headers,
        json={
            "content": (
                "Symptoms: headaches. Sleep: 5 hours. Goals: improve sleep and reduce stress."
            ),
            "source_platform": "chatgpt",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) >= 4
    assert data["confidence"] > 0
