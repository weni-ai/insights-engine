import logging

from django.db.models.query import QuerySet
from django.utils import timezone

from insights.celery import app

from insights.reports.models import Report
from insights.reports.choices import ReportStatus

from insights.metrics.conversations.reports.services import ConversationsReportService


logger = logging.getLogger(__name__)


@app.task
def generate_conversations_report():
    logger.info("[ generate_conversations_report task ] Starting task")
    pending_reports: QuerySet[Report] = Report.objects.filter(status=ReportStatus.PENDING).order_by("created_on")

    if not pending_reports.exists():
        logger.info("[ generate_conversations_report task ] No pending reports found. Finishing task")
        return

    logger.info("[ generate_conversations_report task ] Found %s pending reports", pending_reports.count())

    oldest_report: Report = pending_reports.first()

    logger.info("[ generate_conversations_report task ] Starting generation of oldest report %s", oldest_report.uuid)

    start_time = timezone.now()

    try:
        ConversationsReportService().generate(oldest_report)
    except Exception as e:
        logger.error("[ generate_conversations_report task ] Error generating report %s", oldest_report.uuid, exc_info=True)

    end_time = timezone.now()

    logger.info(
        "[ generate_conversations_report task ] Finished generation of oldest report %s. "
        "Task finished in %s seconds",
        oldest_report.uuid,
        (end_time - start_time).total_seconds(),
    )