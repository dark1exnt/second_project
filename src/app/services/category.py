import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, category_repo: CategoryRepository, session: AsyncSession) -> None:
        self.category_repo = category_repo
        self.session = session

    async def _get_category_or_404(self, category_id: uuid.UUID) -> Category:
        category: Category | None = await self.category_repo.get_by_id(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
            )
        return category

    async def _ensure_category_name_unique(
        self, name: str, exclude_category_id: uuid.UUID | None = None
    ) -> None:
        existing: Category | None = await self.category_repo.get_by_name(name)
        if existing is None:
            return

        if exclude_category_id is not None and existing.id == exclude_category_id:
            return

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Категория с таким именем уже существует"
        )

    async def get_categories(self) -> list[Category]:
        return await self.category_repo.get_all()

    async def get_category(self, category_id: uuid.UUID) -> Category:
        return await self._get_category_or_404(category_id)

    async def create_category(self, payload: CategoryCreate) -> Category:
        await self._ensure_category_name_unique(payload.name)

        try:
            category: Category = await self.category_repo.create(name=payload.name)
            await self.session.commit()
            return category
        except Exception:
            await self.session.rollback()
            raise

    async def update_category(self, category_id: uuid.UUID, payload: CategoryUpdate) -> Category:
        category: Category = await self._get_category_or_404(category_id)

        if payload.name is not None:
            await self._ensure_category_name_unique(
                name=payload.name, exclude_category_id=category.id
            )

        try:
            updated_category: Category = await self.category_repo.update(category, payload)
            await self.session.commit()
            return updated_category
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректные данные категории"
            ) from None
        except Exception:
            await self.session.rollback()
            raise

    async def delete_category(self, category_id: uuid.UUID) -> None:
        category: Category = await self._get_category_or_404(category_id)

        try:
            await self.category_repo.delete(category)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
