from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.health import router as health_router
from app.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.logging import app_logger
from app.core.middleware import AppMiddleware
from app.models import article, category, user  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    app_logger.info(
        "Application starting",
        app_title=settings.app_title,
        app_env=settings.app_env,
        debug=settings.app_debug,
    )
    yield
    app_logger.info("Application stopped")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title, debug=settings.app_debug, lifespan=lifespan)

    app.add_middleware(AppMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Validation error", errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": exc.errors()}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("HTTP exception", status_code=exc.status_code, detail=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(BadRequestError)
    async def bad_request_exception_handler(request: Request, exc: BadRequestError) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Bad request error", detail=exc.detail)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.detail})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_exception_handler(
        request: Request, exc: UnauthorizedError
    ) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Unauthorized error", detail=exc.detail)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": exc.detail}
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Forbidden error", detail=exc.detail)
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": exc.detail})

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Not found error", detail=exc.detail)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.warning("Conflict error", detail=exc.detail)
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = getattr(request.state, "logger", app_logger)
        logger.exception("Unhandled application error", error_type=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(categories_router)
    app.include_router(articles_router)

    return app


app = create_app()
