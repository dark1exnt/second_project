import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
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
            app_logger.warning("Category not found", category_id=str(category_id))
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

        app_logger.warning(
            "Category name conflict",
            category_name=name,
            exclude_category_id=str(exclude_category_id) if exclude_category_id else None,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Категория с таким именем уже существует"
        )

    async def get_categories(self) -> list[Category]:
        app_logger.info("Categories list requested")
        return await self.category_repo.get_all()

    async def get_category(self, category_id: uuid.UUID) -> Category:
        app_logger.info("Category requested", category_id=str(category_id))
        return await self._get_category_or_404(category_id)

    async def create_category(self, payload: CategoryCreate) -> Category:
        logger = app_logger.bind(category_name=payload.name)
        logger.info("Category create started")

        await self._ensure_category_name_unique(payload.name)

        try:
            category: Category = await self.category_repo.create(name=payload.name)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            logger.exception("Category create failed")
            raise

        logger.info("Category create successfully", category_id=str(category.id))
        return category

    async def update_category(self, category_id: uuid.UUID, payload: CategoryUpdate) -> Category:
        logger = app_logger.bind(category_id=str(category_id))
        logger.info("Category update started")

        category: Category = await self._get_category_or_404(category_id)

        if payload.name is not None:
            await self._ensure_category_name_unique(
                name=payload.name, exclude_category_id=category.id
            )

        try:
            updated_category: Category = await self.category_repo.update(category, payload)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            logger.warning("Category update rejected: invalid data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректные данные категории"
            ) from None
        except Exception:
            await self.session.rollback()
            logger.exception("Category update failed")
            raise

        logger.info("Category updated successfully", category_id=str(updated_category.id))
        return updated_category

    async def delete_category(self, category_id: uuid.UUID) -> None:
        logger = app_logger.bind(category_id=str(category_id))
        logger.info("Category delete started")

        category: Category = await self._get_category_or_404(category_id)

        try:
            await self.category_repo.delete(category)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            logger.exception("Category delete failed")
            raise

        logger.info("Category delete successfully", category_id=str(category_id))
