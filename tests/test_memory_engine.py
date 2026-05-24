"""API tests for Behavioural Memory Engine."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_memory(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Frequent headaches in the morning"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["category"] == "health"
    memory_id = body["id"]

    get_one = await client.get(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers,
    )
    assert get_one.status_code == 200
    assert get_one.json()["content"] == "Frequent headaches in the morning"


@pytest.mark.asyncio
async def test_list_memories_with_category_filter(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Runs 3x per week"},
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "communication", "content": "Prefers bullet points"},
    )

    filtered = await client.get(
        "/api/v1/memory?category=behaviour",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert all(m["category"] == "behaviour" for m in filtered.json())


@pytest.mark.asyncio
async def test_update_memory(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Low hydration"},
    )
    memory_id = create.json()["id"]

    update = await client.put(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers,
        json={"content": "Drinks 8 glasses of water daily"},
    )
    assert update.status_code == 200
    assert update.json()["content"] == "Drinks 8 glasses of water daily"


@pytest.mark.asyncio
async def test_semantic_search(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Studies late until 2am before exams"},
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Afternoon fatigue and headaches"},
    )

    search = await client.post(
        "/api/v1/memory/search",
        headers=auth_headers,
        json={"query": "sleep deprivation and fatigue", "limit": 5},
    )
    assert search.status_code == 200
    data = search.json()
    assert data["query"] == "sleep deprivation and fatigue"
    assert "results" in data
    assert data["total"] >= 1
    assert data["results"][0]["relevance_score"] > 0
    assert "steps" in data
    assert len(data["steps"]) >= 3


@pytest.mark.asyncio
async def test_summarize_memories(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "health", "content": "Wants to improve sleep quality"},
    )
    await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "behaviour", "content": "Skips breakfast on busy days"},
    )

    summary = await client.post(
        "/api/v1/memory/summarize",
        headers=auth_headers,
        json={"max_memories": 50},
    )
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_memories"] >= 2
    assert len(data["overall_summary"]) > 10
    assert len(data["by_category"]) >= 1
    assert "steps" in data


@pytest.mark.asyncio
async def test_delete_memory(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create = await client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"category": "recommendation", "content": "Tried melatonin supplement"},
    )
    memory_id = create.json()["id"]

    delete = await client.delete(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers,
    )
    assert delete.status_code == 204

    get_one = await client.get(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers,
    )
    assert get_one.status_code == 404


@pytest.mark.asyncio
async def test_memory_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/memory")
    assert response.status_code == 401
