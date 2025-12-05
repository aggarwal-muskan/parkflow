from celery import Celery
from celery.schedules import crontab
from backend.config import Config

celery = Celery(
    "vehicle_parking_app",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
)

# Timezone settings
celery.conf.timezone = "Asia/Kolkata"
celery.conf.enable_utc = True
celery.conf.worker_pool = "solo"

import backend.tasks.export       # noqa: F401
import backend.tasks.reminders    # if you created it  # noqa: F401
import backend.tasks.reports

celery.conf.beat_schedule = {
    "daily-reminder-job": {
        "task": "backend.tasks.reminders.daily_user_reminder",
        "schedule": crontab(hour=18, minute=0),  # 6 PM
    },
    "monthly-report-job": {
        "task": "backend.tasks.reports.monthly_report",
        "schedule": crontab(day_of_month=1, hour=9, minute=0),  # 1st each month
    },
}
