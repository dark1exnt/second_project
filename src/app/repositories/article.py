import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, DeletedArticle
from app.models.category import Category
from app.schemas.article import ArticleUpdate
from app.schemas.category import CategoryUpdate


class ArticleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_list(
        self,
        page_number: int,
        page_size: int,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
    ) -> tuple[list[Article], int]:
        query = select(Article).options(selectinload(Article.category))

        if search:
            ts_query = func.plainto_tsquery("russian", search)
            query = query.where(Article.search_vector.op("@@")(ts_query))

        if category_id:
            query = query.where(Article.category_id == category_id)

        count_query = select(func.count()).select_from(query.subquery())
        total: int = (await self.db.execute(count_query)).scalar_one()

        offset = (page_number - 1) * page_size
        query = query.order_by(Article.created_at.desc()).offset(offset).limit(page_size)
        rows = (await self.db.execute(query)).scalars().all()
        return list(rows), total

    async def get_by_id(self, article_id: uuid.UUID) -> Article | None:
        result = await self.db.execute(
            select(Article).options(selectinload(Article.category)).where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        title: str,
        content: str,
        author_id: uuid.UUID,
        category_id: uuid.UUID | None,
        image_url: str | None,
    ) -> Article:
        article = Article(
            title=title,
            content=content,
            author_id=author_id,
            category_id=category_id,
            image_url=image_url,
        )
        self.db.add(article)
        await self.db.flush()
        await self.db.execute(
            text(
                """
                UPDATE articles SET search_vector = to_tsvector('russian', :title || ' ' || :content)
                WHERE id = :id
                """
            ),
            {"title": title, "content": content, "id": str(article.id)},
        )
        await self.db.refresh(article)
        result = await self.db.execute(
            select(Article).options(selectinload(Article.category)).where(Article.id == article.id)
        )
        return result.scalar_one()

    async def update(self, article: Article, data: ArticleUpdate) -> Article:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(article, key, value)
        self.db.add(article)
        await self.db.flush()
        if "title" in update_data or "content" in update_data:
            await self.db.execute(
                text(
                    """
                    UPDATE articles SET search_vector = to_tsvector('russian', :title || ' ' || :content)
                    WHERE id = :id
                    """
                ),
                {"title": article.title, "content": article.content, "id": str(article.id)},
            )
        await self.db.refresh(article)
        return article

    async def soft_delete(self, article: Article) -> None:
        deleted = DeletedArticle(
            original_id=article.id,
            title=article.title,
            content=article.content,
            image_url=article.image_url,
            author_id=article.author_id,
            category_id=article.category_id,
        )
        self.db.add(deleted)
        await self.db.delete(article)
        await self.db.flush()


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Category]:
        result = await self.db.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def create(self, name: str, slug: str) -> Category:
        category = Category(name=name, slug=slug)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.flush()
