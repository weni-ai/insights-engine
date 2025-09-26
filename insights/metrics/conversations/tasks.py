import logging
from datetime import timedelta

from django.db.models import Q
from django.db.models.query import QuerySet
from django.conf import settings
from django.utils import timezone

from insights.celery import app

from insights.reports.models import Report
from insights.reports.choices import ReportStatus
from insights.sources.cache import CacheClient
from insights.sources.dl_events.clients import DataLakeEventsClient
from insights.metrics.conversations.reports.services import ConversationsReportService
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.integrations.elasticsearch.clients import (
    ElasticsearchClient,
)


logger = logging.getLogger(__name__)


@app.task
def generate_conversations_report():
    host = settings.HOSTNAME

    logger.info("[ generate_conversations_report task ] Starting task in host %s", host)

    if (
        Report.objects.filter(status=ReportStatus.IN_PROGRESS).count()
        >= settings.REPORT_GENERATION_MAX_CONCURRENT_REPORTS
    ):
        logger.info(
            "[ generate_conversations_report task ] Maximum number (%s) of concurrent reports being generated reached. Finishing task",
            settings.REPORT_GENERATION_MAX_CONCURRENT_REPORTS,
        )
        return

    interrupted_reports: QuerySet[Report] = Report.objects.filter(
        Q(config__interrupted=True) & ~Q(config__interrupted_on_host=host)
    )
    if interrupted_reports.exists():
        logger.info(
            "[ generate_conversations_report task ] Found %s interrupted reports",
            interrupted_reports.count(),
        )

        oldest_report: Report = interrupted_reports.order_by("created_on").first()

    else:
        pending_reports: QuerySet[Report] = Report.objects.filter(
            status=ReportStatus.PENDING
        ).order_by("created_on")

        if not pending_reports.exists():
            logger.info(
                "[ generate_conversations_report task ] No pending reports found. Finishing task"
            )
            return

        logger.info(
            "[ generate_conversations_report task ] Found %s pending reports",
            pending_reports.count(),
        )

        oldest_report: Report = pending_reports.first()

    if not oldest_report:
        logger.info(
            "[ generate_conversations_report task ] No report to generate. Finishing task"
        )
        return

    logger.info(
        "[ generate_conversations_report task ] Starting generation of oldest report %s",
        oldest_report.uuid,
    )

    start_time = timezone.now()

    try:
        config = oldest_report.config or {}
        config["task_host"] = host
        oldest_report.config = config
        oldest_report.save(update_fields=["config"])
        ConversationsReportService(
            datalake_events_client=DataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(),
            elasticsearch_service=ConversationsElasticsearchService(
                client=ElasticsearchClient(),
            ),
            cache_client=CacheClient(),
        ).generate(oldest_report)
    except Exception as e:
        logger.error(
            "[ generate_conversations_report task ] Error generating report %s: %s",
            oldest_report.uuid,
            str(e),
            exc_info=True,
        )

    end_time = timezone.now()

    logger.info(
        "[ generate_conversations_report task ] Finished generation of oldest report %s. "
        "Task finished in %s seconds",
        oldest_report.uuid,
        (end_time - start_time).total_seconds(),
    )


@app.task
def timeout_reports():
    """
    Timeout reports that are in progress for more than REPORT_GENERATION_TIMEOUT seconds.

    This is a safety mechanism to avoid reports being stuck in progress indefinitely,
    preventing other reports from being generated.

    This should NOT happen, but if it does, the system should be able to fix it by itself
    without human intervention.
    """
    logger.info("[ timeout_reports task ] Starting task")

    in_progress_reports: QuerySet[Report] = Report.objects.filter(
        status=ReportStatus.IN_PROGRESS,
        started_at__lt=timezone.now()
        - timedelta(seconds=settings.REPORT_GENERATION_TIMEOUT),
    )

    if not in_progress_reports.exists():
        logger.info(
            "[ timeout_reports task ] No in progress reports found. Finishing task"
        )
        return

    logger.info(
        "[ timeout_reports task ] Found %s in progress reports",
        in_progress_reports.count(),
    )

    for report in in_progress_reports:
        report.status = ReportStatus.FAILED
        report.completed_at = timezone.now()
        report.errors = {"timeout": "Report generation timed out"}
        report.save(update_fields=["status", "completed_at", "errors"])

    logger.info(
        "[ timeout_reports task ] Timed out %s reports", in_progress_reports.count()
    )
