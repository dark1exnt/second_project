from contextlib import suppress

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserLogin, UserRegister
from app.tasks.email import send_registration_email


class AuthService:
    def __init__(self, user_repo: UserRepository, session: AsyncSession) -> None:
        self.user_repo = user_repo
        self.session = session

    async def register(self, payload: UserRegister) -> User:
        existing_user_by_email: User | None = await self.user_repo.get_by_email(payload.email)
        if existing_user_by_email is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован"
            )

        existing_user_by_username: User | None = await self.user_repo.get_by_username(
            payload.username
        )
        if existing_user_by_username is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя уже занято"
            )

        hashed_password: str = hash_password(payload.password)

        try:
            user: User = await self.user_repo.create(
                email=payload.email,
                username=payload.username,
                hashed_password=hashed_password,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        with suppress(Exception):
            send_registration_email.delay(user.email, user.username)

        return user

    async def login(self, payload: UserLogin) -> str:
        user: User | None = await self.user_repo.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильный логин или пароль"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь неактивен"
            )

        access_token: str = create_access_token(subject=str(user.id))
        return access_token
