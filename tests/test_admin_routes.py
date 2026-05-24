import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.user import User
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_admin_simulations_requires_admin(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(
        "/api/v1/admin/simulations",
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_simulations_list(
    client: AsyncClient, auth_headers: dict[str, str]
):
    async with TestSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.email == "test@example.com")
            .values(is_admin=True)
        )
        await session.commit()

    response = await client.get(
        "/api/v1/admin/simulations",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
