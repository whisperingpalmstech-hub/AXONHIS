"""Celery worker for async task processing."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "axonhis",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=[
        "app.core.analytics.tasks"
    ],
    beat_schedule={
        "daily-analytics-crunch": {
            "task": "axonhis.analytics.daily_crunch",
            "schedule": crontab(minute=0, hour=0),  # Runs at midnight UTC
        }
    }
)


@celery_app.task(name="axonhis.health")
def health_check() -> dict:
    return {"status": "ok", "worker": "axonhis"}
