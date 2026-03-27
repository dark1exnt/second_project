import io
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.repositories.article import ArticleRepository
from app.schemas.article import ArticleUpdate
from app.services.s3 import s3_service


class ArticleService:
    def __init__(self, article_repo: ArticleRepository, session: AsyncSession) -> None:
        self.article_repo = article_repo
        self.session = session

    async def _get_article_or_404(self, article_id: uuid.UUID) -> Article:
        article: Article | None = await self.article_repo.get_by_id(article_id)
        if article is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
        return article

    def _check_author(self, article: Article, current_user_id: uuid.UUID) -> None:
        if article.author_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    async def get_articles(
        self, page: int, page_size: int, search: str | None, category_id: uuid.UUID | None
    ) -> tuple[list[Article], int]:
        articles, total = await self.article_repo.get_list(
            page_number=page, page_size=page_size, search=search, category_id=category_id
        )
        return articles, total

    async def get_article(self, article_id: uuid.UUID) -> Article:
        article: Article = await self._get_article_or_404(article_id)
        return article

    async def create_article(
        self, title: str, content: str, author_id: uuid.UUID, category_id: uuid.UUID | None
    ) -> Article:
        try:
            article = await self.article_repo.create(
                title=title,
                content=content,
                author_id=author_id,
                category_id=category_id,
                image_url=None,
            )
            await self.session.commit()
            return article
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Категория не найдена"
            ) from None
        except Exception:
            await self.session.rollback()
            raise

    async def update_article(
        self, article_id: uuid.UUID, payload: ArticleUpdate, current_user_id: uuid.UUID
    ) -> Article:
        article: Article = await self._get_article_or_404(article_id)

        self._check_author(article, current_user_id)
        try:
            updated_article: Article = await self.article_repo.update(article, payload)
            await self.session.commit()
            return updated_article
        except Exception:
            await self.session.rollback()
            raise

    async def delete_article(self, article_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        article: Article = await self._get_article_or_404(article_id)

        self._check_author(article, current_user_id)

        try:
            await self.article_repo.soft_delete(article)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def upload_article_image(
        self, article_id: uuid.UUID, file: UploadFile, current_user_id: uuid.UUID
    ) -> Article:
        article: Article = await self._get_article_or_404(article_id)

        self._check_author(article, current_user_id)

        contents: bytes = await file.read()

        ext_map = {"image/png": "png", "image/webp": "webp", "image/jpeg": "jpg"}
        if file.content_type not in ext_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Неподдерживаемый тип файла"
            )
        ext: str = ext_map[file.content_type]

        image_url: str = s3_service.upload_image(
            file=io.BytesIO(contents), content_type=file.content_type, ext=ext
        )

        try:
            updated_article: Article = await self.article_repo.update(
                article, ArticleUpdate(image_url=image_url)
            )
            await self.session.commit()
            return updated_article
        except Exception:
            await self.session.rollback()
            raise
