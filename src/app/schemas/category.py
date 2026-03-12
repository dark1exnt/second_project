from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
