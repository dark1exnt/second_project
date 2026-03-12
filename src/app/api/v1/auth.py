from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.tasks.email import send_registration_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> UserResponse:
    repo = UserRepository(db)

    if await repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован"
        )

    if await repo.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя уже занято"
        )

    user = await repo.create(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )

    send_registration_email.delay(user.email, user.username)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильный логин или пароль"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь неактивен"
        )

    token = create_access_token(subject=str(user.id))

    response.set_cookie(
        key="access_token", value=token, httponly=True, samesite="lax", secure=False
    )

    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("access_token")
    return {"detail": "Вы вышли из системы"}
