import os
from celery import Celery
import structlog
from config import settings

logger = structlog.get_logger(__name__)

redis_url = settings.REDIS_URL

celery_app = Celery("intelli_credit_tasks", broker=redis_url, backend=redis_url, include=['tasks'])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_publish_retry=True,
)
