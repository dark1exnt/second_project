import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.article import ArticleRepository
from app.schemas.article import ArticleCreate, ArticleListResponse, ArticleResponse, ArticleUpdate
from app.services.s3 import s3_service

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=ArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    repo = ArticleRepository(db)
    articles, total = await repo.get_list(
        page_number=page, page_size=page_size, search=search, category_id=category_id
    )
    return ArticleListResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ArticleResponse:
    repo = ArticleRepository(db)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
    return ArticleResponse.model_validate(article)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleResponse:
    repo = ArticleRepository(db)
    try:
        article = await repo.create(
            title=payload.title,
            content=payload.content,
            author_id=current_user.id,
            category_id=payload.category_id,
            image_url=None,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Категория не найдена"
        ) from None

    return ArticleResponse.model_validate(article)


@router.post("/{article_id}/image", response_model=ArticleResponse)
async def upload_article_image(
    article_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleResponse:
    repo = ArticleRepository(db)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    contents = await file.read()
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    image_url = s3_service.upload_image(
        file=io.BytesIO(contents), content_type=file.content_type or "image/jpeg", ext=ext
    )

    article = await repo.update(article, ArticleUpdate(image_url=image_url))
    return ArticleResponse.model_validate(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = ArticleRepository(db)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    await repo.soft_delete(article)


@router.patch("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleResponse:
    repo = ArticleRepository(db)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    article = await repo.update(article, payload)
    return ArticleResponse.model_validate(article)
