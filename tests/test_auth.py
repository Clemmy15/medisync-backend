import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alice", "email": "alice@test.com", "password": "securepass1"},
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == "alice@test.com"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@test.com", "password": "securepass1"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/profile")
    assert response.status_code == 401
