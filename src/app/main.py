from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.health import router as health_router
from app.config import settings
from app.core.middleware import JWTAuthMiddleware
from app.models import article, category, user  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title, debug=settings.app_debug)

    app.add_middleware(JWTAuthMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(categories_router)
    app.include_router(articles_router)

    return app


app = create_app()
