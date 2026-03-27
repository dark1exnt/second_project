from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.article import ArticleRepository
from app.repositories.category import CategoryRepository
from app.repositories.user import UserRepository
from app.services.article import ArticleService
from app.services.auth import AuthService
from app.services.category import CategoryService


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, session=db)


def get_article_repository(db: AsyncSession = Depends(get_db)) -> ArticleRepository:
    return ArticleRepository(db)


def get_article_service(
    db: AsyncSession = Depends(get_db),
    article_repo: ArticleRepository = Depends(get_article_repository),
) -> ArticleService:
    return ArticleService(article_repo=article_repo, session=db)


def get_category_repository(db: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_category_service(
    db: AsyncSession = Depends(get_db),
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> CategoryService:
    return CategoryService(category_repo=category_repo, session=db)
