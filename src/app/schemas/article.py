from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.schemas.category import CategoryResponse


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category_id: uuid.UUID | None = None


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    category_id: uuid.UUID | None = None
    image_url: str | None = None


class ArticleResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    image_url: str | None
    author_id: uuid.UUID
    category_id: uuid.UUID | None
    category: CategoryResponse | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
