import uuid

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


async def get_current_user(
    access_token: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные"
    )

    if access_token is None:
        raise credentials_exception from None

    try:
        user_id = decode_access_token(access_token)
    except JWTError:
        raise credentials_exception from None

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))

    if user is None:
        raise credentials_exception from None

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неактивный пользователь")

    return user
