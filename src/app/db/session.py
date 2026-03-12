from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(str(settings.database_url), echo=settings.app_debug)

asyncsessionfactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with asyncsessionfactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
