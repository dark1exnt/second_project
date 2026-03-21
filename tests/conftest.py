from typing import AsyncGenerator, Generator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
from app.db.session import get_db, asyncsessionfactory
from app.main import app


@pytest.fixture(autouse=True)
def mock_celery() -> Generator[None, None, None]:
    with patch("app.api.v1.auth.send_registration_email.delay"):
        yield


@pytest.fixture
async def client(mock_celery) -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async def override_get_db() ->  AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE deleted_articles, articles, categories, users CASCADE")
        )
    await engine.dispose()


@pytest.fixture
async def second_client(mock_celery) -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async def override_get_db() ->  AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE deleted_articles, articles, categories, users CASCADE")
        )
    await engine.dispose()


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    await client.post("/auth/register",
                      json={
                          "email": "pytest@example.com",
                          "username": "testuser",
                          "password": "testpassword123"
                      })
    response = await client.post("/auth/login", json={
        "email": "pytest@example.com",
        "password": "testpassword123"
    })

    assert response.status_code == 200
    return client


@pytest.fixture
async def second_auth_client(second_client: AsyncClient) -> AsyncClient:
    await second_client.post("/auth/register",
                      json={
                          "email": "second@example.com",
                          "username": "seconduser",
                          "password": "testpassword123"
                      })
    response = await second_client.post("/auth/login", json={
        "email": "second@example.com",
        "password": "testpassword123"
    })

    assert response.status_code == 200
    return second_client