import uuid

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_category_service
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryResponse])
async def get_categories(
    category_service: CategoryService = Depends(get_category_service),
) -> list[CategoryResponse]:
    return await category_service.get_categories()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID, category_service: CategoryService = Depends(get_category_service)
) -> CategoryResponse:
    return await category_service.get_category(category_id)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    return await category_service.create_category(payload)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    return await category_service.update_category(category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
) -> None:
    return await category_service.delete_category(category_id)
