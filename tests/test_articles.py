import pytest
from httpx import AsyncClient
from unittest.mock import patch


async def create_category(client: AsyncClient, name: str = "Technology") -> str:
    response = await client.post("/categories/", json={"name": name})
    return response.json()["id"]


async def create_article(
    client: AsyncClient,
    category_id: str,
    title: str = "Test Article",
    content: str = "Test content"
) -> dict:
    response = await client.post("/articles/", json={
        "title": title,
        "content": content,
        "category_id": category_id
    })
    return response.json()


@pytest.mark.asyncio
async def test_create_article(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    response = await auth_client.post("/articles/", json={
        "title": "Test Article",
        "content": "Test content",
        "category_id": category_id        
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Article"
    assert data["content"] == "Test content"
    assert data["category"]["id"] == category_id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_article_without_category(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/articles/", json={
        "title": "Test Article",
        "content": "Test content",
        "category_id": None    
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_article_invalid_category(auth_client: AsyncClient) -> None:
    response = await auth_client.post("/articles/", json={
        "title": "Test Article",
        "content": "Test content",
        "category_id": "00000000-0000-0000-0000-000000000000"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_article_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/articles/", json={
        "title": "Test Article",
        "content": "Test content",
        "category_id": None    
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_articles(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    await create_article(auth_client, category_id, title="Article 1")
    await create_article(auth_client, category_id, title="Article 2")

    response = await auth_client.get("/articles/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert "total_pages" in data


@pytest.mark.asyncio
async def test_get_articles_empty(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/articles/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_articles_pagination(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    for i in range(5):
        await create_article(auth_client, category_id, title=f"Article {i}")
    
    response = await auth_client.get("/articles/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_articles_filter_by_category(auth_client: AsyncClient) -> None:
    cat1_id = await create_category(auth_client, "Technology")
    cat2_id = await create_category(auth_client, "Medicine")
    await create_article(auth_client, cat1_id, title="Technology Article")
    await create_article(auth_client, cat2_id, title="Medicine Article")

    response = await auth_client.get(f"/articles/?category_id={cat1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Technology Article"


@pytest.mark.asyncio
async def test_get_articles_search(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    await create_article(auth_client, category_id, title="Some title text", content="Content 1")
    await create_article(auth_client, category_id, title="Title 2", content="Content 2")

    response = await auth_client.get("/articles/?search=text")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Some title text"


@pytest.mark.asyncio
async def test_get_article_by_id(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    response = await auth_client.get(f"/articles/{article_id}")
    assert response.status_code == 200
    assert response.json()["id"] == article_id


@pytest.mark.asyncio
async def test_get_article_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_article(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    response = await auth_client.patch(f"/articles/{article_id}", json={
        "title": "Updated title",
        "content": "Updated content"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"

@pytest.mark.asyncio
async def test_update_article_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.patch("/articles/00000000-0000-0000-0000-000000000000", json={"title": "Updated title"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_article_requires_auth(client: AsyncClient) -> None:
    response = await client.patch("/articles/00000000-0000-0000-0000-000000000000", json={"title": "Updated title"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_article_forbidden(auth_client: AsyncClient, second_auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)

    response = await second_auth_client.patch(f"/articles/{article["id"]}", json={"title": "test_update_article_forbidden"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_article_image(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    with patch("app.api.v1.articles.s3_service.upload_image", return_value="https://s3/image.jpg"):
        response = await auth_client.post(
            f"/articles/{article_id}/image",
            files={"file": ("image.jpg", b"fake image content", "image/jpeg")}
        )
    assert response.status_code == 200
    assert response.json()["image_url"] == "https://s3/image.jpg"    


@pytest.mark.asyncio
async def test_upload_image_forbidden(auth_client: AsyncClient, second_auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    with patch("app.api.v1.articles.s3_service.upload_image", return_value="https://s3/image.jpg"):
        response = await second_auth_client.post(
            f"/articles/{article_id}/image",
            files={"file": ("image.jpg", b"fake image content", "image/jpeg")}
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_article(auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    response = await auth_client.delete(f"/articles/{article_id}")
    assert response.status_code == 204

    response = await auth_client.delete(f"/articles/{article_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_article_not_found(auth_client: AsyncClient) -> None:
    response = await auth_client.delete("/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_article_requires_auth(client: AsyncClient) -> None:
    response = await client.delete("/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_article_forbidden(auth_client: AsyncClient, second_auth_client: AsyncClient) -> None:
    category_id = await create_category(auth_client)
    article = await create_article(auth_client, category_id)
    article_id = article["id"]

    response = await second_auth_client.delete(f"/articles/{article_id}")
    assert response.status_code == 403
