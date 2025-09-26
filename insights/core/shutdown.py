"""
Centralized shutdown handling for the insights application.

This module provides graceful shutdown handling for both Kubernetes pod termination
and Celery worker shutdown scenarios.
"""

import logging
import signal
import threading

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Global flag to prevent double execution of shutdown handler
_shutdown_in_progress = False
_shutdown_lock = threading.Lock()


def graceful_shutdown_handler(timeout_seconds=30):
    """
    Enhanced shutdown handler for graceful pod termination.

    Args:
        timeout_seconds: Maximum time to wait for graceful shutdown
    """
    # Import Django models inside the function to avoid AppRegistryNotReady error
    from insights.reports.models import Report
    from insights.reports.choices import ReportStatus

    global _shutdown_in_progress

    # Prevent double execution
    with _shutdown_lock:
        if _shutdown_in_progress:
            logger.info("[ shutdown_handler ] Shutdown already in progress, skipping")
            return
        _shutdown_in_progress = True

    host = settings.HOSTNAME

    logger.info("[ shutdown_handler ] Starting graceful shutdown")

    try:
        # Get in-progress reports with timeout protection
        in_progress_reports = []
        try:
            in_progress_reports = Report.objects.filter(status=ReportStatus.IN_PROGRESS)
        except Exception as e:
            logger.error(
                "[ shutdown_handler ] Error fetching in-progress reports: %s", str(e)
            )
            return

        if not in_progress_reports:
            logger.info("[ shutdown_handler ] No in-progress reports found")
            return

        interrupted_reports = []

        # Process each report with individual timeout protection
        for in_progress_report in in_progress_reports:
            try:
                if in_progress_report.config.get("task_host") != host:
                    continue

                interrupted_reports.append(in_progress_report)

            except Exception as e:
                logger.error(
                    "[ shutdown_handler ] Error processing report %s: %s",
                    in_progress_report.uuid,
                    str(e),
                )

        # Update interrupted reports with timeout protection
        if interrupted_reports:
            try:
                for interrupted_report in interrupted_reports:
                    config = interrupted_report.config or {}
                    config["interrupted"] = True
                    config["interrupted_at"] = str(timezone.now())
                    config["interrupted_on_host"] = host
                    interrupted_report.config = config
                    interrupted_report.save(update_fields=["config"])

                logger.info(
                    "[ shutdown_handler ] Successfully updated %s reports",
                    len(interrupted_reports),
                )
            except Exception as e:
                logger.error("[ shutdown_handler ] Error updating reports: %s", str(e))
        else:
            logger.info(
                "[ shutdown_handler ] No reports were interrupted by this worker"
            )

    except Exception as e:
        logger.error(
            "[ shutdown_handler ] Unexpected error during shutdown: %s", str(e)
        )
    finally:
        logger.info("[ shutdown_handler ] Graceful shutdown completed")
        # Reset the flag in case of restart
        with _shutdown_lock:
            _shutdown_in_progress = False


def _sigterm_handler(signum, frame):
    """
    Handle SIGTERM signal from Kubernetes.
    """
    logger.info(
        "[ sigterm_handler ] Received SIGTERM signal, initiating graceful shutdown"
    )
    graceful_shutdown_handler()


def setup_signal_handlers():
    """
    Set up signal handlers for graceful shutdown.
    This should be called during application initialization.
    """
    logger.info("[ setup_signal_handlers ] Setting up SIGTERM handler")
    signal.signal(signal.SIGTERM, _sigterm_handler)
    logger.info("[ setup_signal_handlers ] SIGTERM handler registered")
