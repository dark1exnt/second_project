from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_auth_service
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister, auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    user = await auth_service.register(payload)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin, response: Response, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    access_token: str = await auth_service.login(payload)

    response.set_cookie(
        key="access_token", value=access_token, httponly=True, samesite="lax", secure=False
    )

    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=False)
    return {"detail": "Вы вышли из системы"}
