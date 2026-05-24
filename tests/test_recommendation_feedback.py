"""Recommendation save and helpful feedback."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_save_and_helpful_recommendation(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/profile",
        headers=auth_headers,
        json={"age_range": "25-34", "occupation": "Student"},
    )
    gen = await client.post(
        "/api/v1/recommendations/generate",
        headers=auth_headers,
        json={},
    )
    assert gen.status_code == 200

    history = await client.get(
        "/api/v1/recommendations/history",
        headers=auth_headers,
        params={"limit": 1},
    )
    rec_id = history.json()[0]["id"]

    save = await client.post(
        f"/api/v1/recommendations/{rec_id}/save",
        headers=auth_headers,
    )
    assert save.status_code == 200
    assert save.json()["is_saved"] is True
    assert save.json()["memory_created"] is True

    helpful = await client.post(
        f"/api/v1/recommendations/{rec_id}/helpful",
        headers=auth_headers,
    )
    assert helpful.status_code == 200
    assert helpful.json()["marked_helpful"] is True

    updated = await client.get(
        "/api/v1/recommendations/history",
        headers=auth_headers,
        params={"limit": 1},
    )
    item = updated.json()[0]
    assert item["is_saved"] is True
    assert item["marked_helpful"] is True
