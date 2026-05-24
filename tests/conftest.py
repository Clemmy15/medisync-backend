import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

# Allow tests without a compiled chromadb/hnswlib wheel (e.g. Windows dev boxes).
if "chromadb" not in sys.modules:
    _chromadb = MagicMock()
    _chromadb_config = MagicMock()
    _chromadb_config.Settings = MagicMock
    sys.modules["chromadb"] = _chromadb
    sys.modules["chromadb.config"] = _chromadb_config

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = (
    "sqlite+aiosqlite:///file:medisync_test?mode=memory&cache=shared&uri=true"
)
os.environ["LLM_PROVIDER"] = "mock"
os.environ["DEBUG"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.core.config import get_settings

get_settings.cache_clear()

from app.database.base import Base
from app.database.session import get_db
from main import create_app

TEST_DATABASE_URL = (
    "sqlite+aiosqlite:///file:medisync_test?mode=memory&cache=shared&uri=true"
)

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
