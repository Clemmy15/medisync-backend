"""Production security middleware and configuration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_on_response(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient) -> None:
    import os

    if os.environ.get("RATE_LIMIT_ENABLED", "true").lower() != "true":
        pytest.skip("Rate limiting disabled in test environment")
    response = await client.get("/health")
    assert response.headers.get("X-RateLimit-Limit") is not None
    assert response.headers.get("X-RateLimit-Remaining") is not None


@pytest.mark.asyncio
async def test_weak_password_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Weak Pass",
            "email": "weak@example.com",
            "password": "abcdefgh",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code in (200, 503)
