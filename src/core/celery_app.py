import os
from celery import Celery
from celery.schedules import crontab

# Celery Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "legal_ai_celery",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.tasks.data_pipeline", "src.tasks.async_review"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
)

# Setup Celery Beat
celery_app.conf.beat_schedule = {
    "run_daily_data_pipeline": {
        "task": "src.tasks.data_pipeline.run_pipeline",
        "schedule": crontab(hour=2, minute=0), # 2 AM everyday
    },
}
