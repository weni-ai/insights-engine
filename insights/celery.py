import os
import logging

from celery import Celery

logger = logging.getLogger(__name__)

# Set the default Django settings module for the "celery" program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insights.settings")

app = Celery("insights")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace="CELERY" means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


logger.info("Starting task discovery...")
app.autodiscover_tasks()
logger.info("Task discovery completed")

logger.info("Discovered tasks: %s", list(app.tasks.keys()))

app.conf.beat_schedule = {
    "test": {
        "task": "insights.projects.tasks.test",
        "schedule": (10),  # 10 seconds
        "args": ("Test task",),
    },
}
