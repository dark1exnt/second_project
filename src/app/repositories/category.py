import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryUpdate


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Category]:
        result = await self.db.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def create(self, name: str) -> Category:
        category = Category(name=name)
        self.db.add(category)
        await self.db.flush()
        return category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        self.db.add(category)
        await self.db.flush()
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.flush()
