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


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob",
            "email": "bob@test.com",
            "password": "oldpass123",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@test.com", "password": "oldpass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    bad = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "newpass123"},
    )
    assert bad.status_code == 401

    ok = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "oldpass123", "new_password": "newpass123"},
    )
    assert ok.status_code == 204

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@test.com", "password": "newpass123"},
    )
    assert new_login.status_code == 200
