import os
import logging

from celery import Celery
from celery.signals import worker_shutting_down

logger = logging.getLogger(__name__)

# Set the default Django settings module for the "celery" program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insights.settings")

app = Celery("insights")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace="CELERY" means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


# Register Celery worker shutdown handler
@worker_shutting_down.connect
def celery_shutdown_handler(sender, **kwargs):
    """
    Handle Celery worker shutdown signal.
    """
    # Import here to avoid AppRegistryNotReady error
    from insights.core.shutdown import graceful_shutdown_handler

    logger.info("[ celery_shutdown_handler ] Celery worker shutdown signal received")
    graceful_shutdown_handler()


# Note: Signal handlers are set up in the shutdown module when needed
# We only set up the Celery worker shutdown handler here


logger.info("Starting task discovery...")
app.autodiscover_tasks()

logger.info("Task discovery completed")

logger.info("Discovered tasks: %s", list(app.tasks.keys()))

app.conf.beat_schedule = {
    "activate-indexer": {
        "task": "insights.projects.tasks.activate_indexer",
        "schedule": (60 * 60),  # 1 hour
    },
    "generate-conversations-report": {
        "task": "insights.metrics.conversations.tasks.generate_conversations_report",
        "schedule": 10,  # 10 seconds
    },
    "timeout-reports": {
        "task": "insights.metrics.conversations.tasks.timeout_reports",
        "schedule": 30,  # 30 seconds
    },
}
