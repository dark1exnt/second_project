import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={
        "email": "test_register_success@example.com",
        "username": "test_register_success_user",
        "password": "testpassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test_register_success@example.com"
    assert data["username"] == "test_register_success_user"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post("/auth/register", json={
        "email": "test_register_duplicate_email@example.com",
        "username": "test_register_duplicate_email_user1",
        "password": "testpassword123"
        })
    response = await client.post("/auth/register", json={
        "email": "test_register_duplicate_email@example.com",
        "username": "test_register_duplicate_email_user2",
        "password": "testpassword123"        
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post("/auth/register", json={
        "email": "test_login_success@example.com",
        "username": "test_login_success_user",
        "password": "testpassword123"             
    })
    response = await client.post("/auth/login", json={
        "email": "test_login_success@example.com",
        "password": "testpassword123"         
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post("/auth/register", json={
        "email": "test_login_wrong_password@example.com",
        "username": "test_login_wrong_password_user",
        "password": "testpassword123"           
    })
    response = await client.post("/auth/login", json={
        "email": "test_login_wrong_password@example.com",
        "password": "wrongpassword"         
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/auth/logout")
    assert response.status_code == 200