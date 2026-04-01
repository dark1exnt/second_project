from contextlib import suppress

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.logging import app_logger
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
        logger = app_logger.bind(email=payload.email, username=payload.username)
        logger.info("User registration started")

        existing_user_by_email: User | None = await self.user_repo.get_by_email(payload.email)
        if existing_user_by_email is not None:
            logger.warning("User registration rejected: email already exists")
            raise BadRequestError("Email уже зарегистрирован")

        existing_user_by_username: User | None = await self.user_repo.get_by_username(
            payload.username
        )
        if existing_user_by_username is not None:
            logger.warning("User registration rejected: username already exists")
            raise BadRequestError("Имя пользователя уже занято")

        hashed_password: str = hash_password(payload.password)

        try:
            user: User = await self.user_repo.create(
                email=payload.email,
                username=payload.username,
                hashed_password=hashed_password,
            )
        except Exception:
            logger.exception("User registration failed")
            raise

        logger.info("User registered successfully", user_id=str(user.id))

        with suppress(Exception):
            send_registration_email.delay(user.email, user.username)
            logger.info("Registration email task scheduled", user_id=str(user.id))

        return user

    async def login(self, payload: UserLogin) -> str:
        logger = app_logger.bind(email=payload.email)
        logger.info("User login started")

        user: User | None = await self.user_repo.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            logger.warning("User login rejected: invalid credentials")
            raise UnauthorizedError("Неправильный логин или пароль")

        if not user.is_active:
            logger.warning("User login rejected: inactive user", user_id=str(user.id))
            raise BadRequestError("Пользователь неактивен")

        access_token: str = create_access_token(subject=str(user.id))
        logger.info("User login successfully", user_id=str(user.id))
        return access_token
