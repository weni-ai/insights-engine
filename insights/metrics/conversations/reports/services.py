from datetime import timezone
import logging

from insights.reports.services import BaseSourceReportService


from insights.reports.models import Report
from insights.reports.choices import ReportStatus, ReportFormat


logger = logging.getLogger(__name__)


class ConversationsReportService(BaseSourceReportService):
    """
    Service to generate conversations reports.
    """

    def process_csv(self, report: Report) -> None:
        """
        Process the csv for the conversations report.
        """
        pass

    def process_xlsx(self, report: Report) -> None:
        """
        Process the xlsx for the conversations report.
        """
        pass

    def send_email(self, data: dict) -> None:
        """
        Send the email for the conversations report.
        """
        pass

    def start_generation(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Starting generation of conversations report %s",
            report.uuid,
        )

        source_config = report.source_config or {}

        if not source_config:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] source_config is empty for report %s",
                report.uuid,
            )
            raise ValueError(
                "source_config cannot be empty when generating conversations report"
            )

        filters = report.filters or {}

        if not filters:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] filters is empty for report %s",
                report.uuid,
            )
            raise ValueError(
                "filters cannot be empty when generating conversations report"
            )

        sections = source_config.get("sections", [])

        if len(sections) == 0:
            logger.error(
                "[CONVERSATIONS REPORT SERVICE] sections is empty for report %s",
                report.uuid,
            )
            raise ValueError(
                "sections cannot be empty when generating conversations report"
            )

        # custom_widgets = source_config.get("custom_widgets", [])

        report.status = ReportStatus.IN_PROGRESS
        report.started_at = timezone.now()
        report.save(update_fields=["status", "started_at"])

        # TODO: Implement the specific generation logic

        if report.format == ReportFormat.CSV:
            self.process_csv(report)
        elif report.format == ReportFormat.XLSX:
            self.process_xlsx(report)

        report.status = ReportStatus.COMPLETED
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "completed_at"])

        # TODO: Implement the email sending logic
        self.send_email({})
