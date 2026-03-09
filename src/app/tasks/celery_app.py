from celery import Celery

from app.config import settings

celery_app = Celery(
    "blog_marketplace", broker=settings.celery_broker_url, include=["app.tasks.email"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
