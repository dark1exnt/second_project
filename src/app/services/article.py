import io
import uuid

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.logging import app_logger
from app.models.article import Article
from app.repositories.article import ArticleRepository
from app.schemas.article import ArticleUpdate
from app.services.s3 import s3_service


class ArticleService:
    def __init__(self, article_repo: ArticleRepository) -> None:
        self.article_repo = article_repo

    async def _get_article_or_404(self, article_id: uuid.UUID) -> Article:
        article: Article | None = await self.article_repo.get_by_id(article_id)
        if article is None:
            app_logger.warning("Article not found", article_id=str(article_id))
            raise NotFoundError("Статья не найдена")
        return article

    def _check_author(self, article: Article, current_user_id: uuid.UUID) -> None:
        if article.author_id != current_user_id:
            app_logger.warning(
                "Forbidden article access",
                article_id=str(article.id),
                author_id=str(article.author_id),
                current_user_id=str(current_user_id),
            )
            raise ForbiddenError("Нет доступа")

    async def get_articles(
        self, page: int, page_size: int, search: str | None, category_id: uuid.UUID | None
    ) -> tuple[list[Article], int]:
        logger = app_logger.bind(
            page=page,
            page_size=page_size,
            search=search,
            category_id=str(category_id) if category_id else None,
        )
        logger.info("Articles list requested")

        articles, total = await self.article_repo.get_list(
            page_number=page, page_size=page_size, search=search, category_id=category_id
        )
        logger.info("Articles list loaded", total=total)
        return articles, total

    async def get_article(self, article_id: uuid.UUID) -> Article:
        app_logger.info("Article requested", article_id=str(article_id))
        article: Article = await self._get_article_or_404(article_id)
        return article

    async def create_article(
        self, title: str, content: str, author_id: uuid.UUID, category_id: uuid.UUID | None
    ) -> Article:
        logger = app_logger.bind(
            author_id=str(author_id), category_id=str(category_id) if category_id else None
        )
        logger.info("Article create started", title=title)

        try:
            article = await self.article_repo.create(
                title=title,
                content=content,
                author_id=author_id,
                category_id=category_id,
                image_url=None,
            )
        except IntegrityError:
            logger.warning("Article create rejected: category not found")
            raise BadRequestError("Категория не найдена") from None
        except Exception:
            logger.exception("Article create failed")
            raise

        logger.info("Article create successfully", article_id=str(article.id))
        return article

    async def update_article(
        self, article_id: uuid.UUID, payload: ArticleUpdate, current_user_id: uuid.UUID
    ) -> Article:
        logger = app_logger.bind(article_id=str(article_id), current_user_id=str(current_user_id))
        logger.info("Article update started")

        article: Article = await self._get_article_or_404(article_id)
        self._check_author(article, current_user_id)

        try:
            updated_article: Article = await self.article_repo.update(article, payload)
        except Exception:
            logger.exception("Article update failed")
            raise

        logger.info("Article update successfully", article_id=str(updated_article.id))
        return updated_article

    async def delete_article(self, article_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        logger = app_logger.bind(article_id=str(article_id), current_user_id=str(current_user_id))
        logger.info("Article delete started")

        article: Article = await self._get_article_or_404(article_id)
        self._check_author(article, current_user_id)

        try:
            await self.article_repo.soft_delete(article)
        except Exception:
            logger.exception("Article delete failed")
            raise

        logger.info("Article delete successfully", article_id=str(article_id))

    async def upload_article_image(
        self, article_id: uuid.UUID, file: UploadFile, current_user_id: uuid.UUID
    ) -> Article:
        logger = app_logger.bind(
            article_id=str(article_id),
            current_user_id=str(current_user_id),
            filename=file.filename,
            content_type=file.content_type,
        )
        logger.info("Article image upload started")

        article: Article = await self._get_article_or_404(article_id)
        self._check_author(article, current_user_id)

        contents: bytes = await file.read()

        ext_map = {"image/png": "png", "image/webp": "webp", "image/jpeg": "jpg"}
        if file.content_type not in ext_map:
            logger.warning("Article image upload rejected: unsupported file type")
            raise BadRequestError("Неподдерживаемый тип файла")
        ext: str = ext_map[file.content_type]

        image_url: str = s3_service.upload_image(
            file=io.BytesIO(contents), content_type=file.content_type, ext=ext
        )

        try:
            updated_article: Article = await self.article_repo.update(
                article, ArticleUpdate(image_url=image_url)
            )
        except Exception:
            logger.exception("Article image upload failed")
            raise

        logger.info(
            "Article image uploaded successfully",
            article_id=str(updated_article.id),
            image_url=image_url,
        )
        return updated_article
