from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.config import settings
from app.core.middleware import JWTAuthMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title, debug=settings.app_debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(JWTAuthMiddleware)

    app.include_router(health_router)

    return app


app = create_app()
