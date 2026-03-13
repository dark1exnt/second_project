import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/categories/", json={"name": "Technology"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Technology"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_category_duplicate_name(auth_client: AsyncClient) -> None:
    await auth_client.post("/categories/", json={"name": "Technology"})
    response = await auth_client.post("/categories/", json={"name": "Technology"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_category_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/categories/", json={"name": "Technology"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_categories(auth_client: AsyncClient) -> None:
    await auth_client.post("/categories/", json={"name": "Technology"})
    await auth_client.post("/categories/", json={"name": "Medicine"})
    response = await auth_client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_categories_empty(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/categories/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_category_by_id(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/categories/", json={"name": "Technology"})
    category_id = created.json()["id"]

    response = await auth_client.get(f"/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Technology"


@pytest.mark.asyncio
async def test_get_category_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/categories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/categories/", json={"name": "Technology"})
    category_id = created.json()["id"]

    response = await auth_client.patch(f"/categories/{category_id}", json={"name": "Tech"})
    assert response.status_code == 200
    assert response.json()["name"] == "Tech"


@pytest.mark.asyncio
async def test_update_category_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.patch("/categories/00000000-0000-0000-0000-000000000000", json={"name": "Tech"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_requires_auth(client: AsyncClient) -> None:
    response = await client.patch("/categories/00000000-0000-0000-0000-000000000000", json={"name": "Tech"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_category(auth_client: AsyncClient) -> None:
    created = await auth_client.post("/categories/", json={"name": "Technology"})
    category_id = created.json()["id"]

    response = await auth_client.delete(f"/categories/{category_id}")
    assert response.status_code == 204

    response = await auth_client.get(f"/categories/{category_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.delete("/categories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/categories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401
