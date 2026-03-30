from pathlib import Path
import sys

from loguru import logger

from app.config import settings


def setup_logging():
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)

    logger.remove()

    if settings.is_production:
        logger.add(
            sys.stdout,
            level=settings.log_level.upper(),
            serialize=True,
            enqueue=settings.log_enqueue,
            backtrace=True,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level.upper(),
            enqueue=settings.log_enqueue,
            backtrace=True,
            diagnose=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[request_id]}</cyan> | "
                "<cyan>{name}:{function}:{line}</cyan> - "
                "<level>{message}</level>"
            ),
        )

    logger.add(
        Path(settings.log_dir) / "app.log",
        level=settings.log_level.upper(),
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        serialize=settings.is_production,
        enqueue=settings.log_enqueue,
        backtrace=True,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} - "
            "{message} | {extra}"
        ),
    )
    return logger.bind(request_id="-")


app_logger = setup_logging()
