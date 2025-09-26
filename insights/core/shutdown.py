"""
Centralized shutdown handling for the insights application.

This module provides graceful shutdown handling for both Kubernetes pod termination
and Celery worker shutdown scenarios.
"""

import json
import logging
import signal
import threading

from django.conf import settings

from insights.sources.cache import CacheClient
from insights.metrics.conversations.tasks import get_cache_key_for_report

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
    cache_client = CacheClient()

    logger.info("[ shutdown_handler ] Starting graceful shutdown")

    try:
        # Get in-progress reports with timeout protection
        in_progress_reports_uuids = []
        try:
            in_progress_reports_uuids = list(
                Report.objects.filter(status=ReportStatus.IN_PROGRESS).values_list(
                    "uuid", flat=True
                )
            )
        except Exception as e:
            logger.error(
                "[ shutdown_handler ] Error fetching in-progress reports: %s", str(e)
            )
            return

        if not in_progress_reports_uuids:
            logger.info("[ shutdown_handler ] No in-progress reports found")
            return

        interrupted_reports_uuids = []

        # Process each report with individual timeout protection
        for in_progress_report_uuid in in_progress_reports_uuids:
            try:
                key = get_cache_key_for_report(in_progress_report_uuid)
                cached_info = cache_client.get(key)

                if not cached_info:
                    logger.warning(
                        "[ shutdown_handler ] No cache info for report %s, marking as interrupted",
                        in_progress_report_uuid,
                    )
                    interrupted_reports_uuids.append(in_progress_report_uuid)
                    continue

                cached_info = json.loads(cached_info)

                if cached_info.get("host") != host:
                    continue

                interrupted_reports_uuids.append(in_progress_report_uuid)

            except Exception as e:
                logger.error(
                    "[ shutdown_handler ] Error processing report %s: %s",
                    in_progress_report_uuid,
                    str(e),
                )
                # Mark as interrupted to be safe
                interrupted_reports_uuids.append(in_progress_report_uuid)

        # Update interrupted reports with timeout protection
        if interrupted_reports_uuids:
            try:
                Report.objects.filter(uuid__in=interrupted_reports_uuids).update(
                    status=ReportStatus.PENDING,
                )
                logger.info(
                    "[ shutdown_handler ] Successfully reset %s reports to PENDING",
                    len(interrupted_reports_uuids),
                )
            except Exception as e:
                logger.error(
                    "[ shutdown_handler ] Error updating reports to PENDING: %s", str(e)
                )
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
