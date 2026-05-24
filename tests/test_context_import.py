"""API integration tests for Cross-AI Health Context Import."""

import pytest
from httpx import AsyncClient

SAMPLE_CONTEXT = """
Symptoms: Frequent headaches and afternoon fatigue.
Habits: Irregular sleep schedule, walks 2x per week.
Sleep patterns: 5-6 hours on weekdays, catches up on weekends.
Hydration: About 2-3 glasses of water per day.
Stress indicators: Work deadlines, evening anxiety.
Communication preferences: Prefers concise, actionable health tips.
Health goals: Improve sleep quality and reduce stress levels.
"""


@pytest.mark.asyncio
async def test_get_all_platform_prompts(client: AsyncClient) -> None:
    response = await client.get("/api/v1/context-import/prompts")
    assert response.status_code == 200
    data = response.json()
    platforms = {p["platform"] for p in data["platforms"]}
    assert platforms == {"chatgpt", "gemini", "claude"}
    for item in data["platforms"]:
        assert len(item["prompt"]) > 50
        assert len(item["instructions"]) > 20


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", ["chatgpt", "gemini", "claude"])
async def test_get_platform_prompt(client: AsyncClient, platform: str) -> None:
    response = await client.get(f"/api/v1/context-import/prompt/{platform}")
    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == platform
    assert "prompt" in body
    assert "instructions" in body


@pytest.mark.asyncio
async def test_analyze_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/context-import/analyze",
        json={"content": SAMPLE_CONTEXT, "source_platform": "chatgpt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_returns_structured_json(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/context-import/analyze",
        headers=auth_headers,
        json={"content": SAMPLE_CONTEXT, "source_platform": "chatgpt"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "symptoms" in data
    assert "habits" in data
    assert "goals" in data
    assert "confidence" in data
    assert 0.0 < data["confidence"] <= 1.0
    assert "field_confidence" in data
    assert "sleep_patterns" in data["field_confidence"]
    assert data["goals"] == data["health_goals"]
    assert len(data["symptoms"]) >= 1
    assert "steps" in data
    assert len(data["steps"]) >= 4


@pytest.mark.asyncio
async def test_save_persists_to_db_and_memory(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    save_response = await client.post(
        "/api/v1/context-import/save",
        headers=auth_headers,
        json={"content": SAMPLE_CONTEXT, "source_platform": "gemini"},
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["id"] > 0
    assert saved["memories_created"] > 0
    assert saved["extraction"]["confidence"] > 0

    memories = await client.get("/api/v1/memory", headers=auth_headers)
    assert memories.status_code == 200
    assert len(memories.json()) >= 1

    history = await client.get("/api/v1/context-import/history", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) >= 1
    assert history.json()[0]["confidence"] > 0


@pytest.mark.asyncio
async def test_save_with_pre_extracted(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    analyze = await client.post(
        "/api/v1/context-import/analyze",
        headers=auth_headers,
        json={"content": SAMPLE_CONTEXT, "source_platform": "claude"},
    )
    extraction = analyze.json()

    save = await client.post(
        "/api/v1/context-import/save",
        headers=auth_headers,
        json={
            "content": SAMPLE_CONTEXT,
            "source_platform": "claude",
            "extracted": extraction,
        },
    )
    assert save.status_code == 200
    assert save.json()["extraction"]["confidence"] == extraction["confidence"]
