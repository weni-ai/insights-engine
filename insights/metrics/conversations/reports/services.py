from datetime import timezone
import logging
from abc import ABC, abstractmethod

from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import translation


from insights.reports.models import Report
from insights.reports.choices import ReportStatus, ReportFormat, ReportSource
from insights.users.models import User
from insights.projects.models import Project


logger = logging.getLogger(__name__)


class BaseConversationsReportService(ABC):
    """
    Base class for conversations report services.
    """

    @abstractmethod
    def process_csv(self, report: Report) -> None:
        """
        Process the csv for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def process_xlsx(self, report: Report) -> None:
        """
        Process the xlsx for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def send_email(self, report: Report, file_content: str) -> None:
        """
        Send the email for the conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def request_generation(
        self,
        project: Project,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> None:
        """
        Request the generation of a conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def start_generation(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def project_can_receive_new_reports_generation(self, project: Project) -> bool:
        """
        Check if the project can receive new reports generation.
        """
        raise NotImplementedError("Subclasses must implement this method")


class ConversationsReportService(BaseConversationsReportService):
    """
    Service to generate conversations reports.
    """

    def __init__(self):
        self.source = ReportSource.CONVERSATIONS_DASHBOARD

    def process_csv(self, report: Report) -> None:
        """
        Process the csv for the conversations report.
        """

    def process_xlsx(self, report: Report) -> None:
        """
        Process the xlsx for the conversations report.
        """

    def send_email(self, report: Report, file_content: str) -> None:
        """
        Send the email for the conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Sending email for conversations report to %s",
            report.requested_by.email,
        )

        with translation.override(report.requested_by.language):
            subject = _("Conversations dashboard report")
            body = _("Please find the conversations report attached.")

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[report.requested_by.email],
            )

            if report.format == ReportFormat.CSV:
                file_name = f"conversations_report_{report.uuid}.csv"
            elif report.format == ReportFormat.XLSX:
                file_name = f"conversations_report_{report.uuid}.xlsx"

            email.attach(
                file_name,
                file_content,
                (
                    "text/csv"
                    if report.format == ReportFormat.CSV
                    else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
            email.send()

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Email for conversations report %s sent to %s",
            report.uuid,
            report.requested_by.email,
        )

    def request_generation(
        self,
        project: Project,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> None:
        """
        Request the generation of a conversations report.
        """
        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Requesting generation of conversations report for project %s",
            project.uuid,
        )

        report = Report.objects.create(
            project=project,
            source=self.source,
            source_config=source_config,
            filters=filters,
            format=report_format,
            requested_by=requested_by,
        )

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Conversations report created %s",
            report.uuid,
        )

        return report

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

        # TODO: Implement the email sending logic
        self.send_email({})

        report.status = ReportStatus.COMPLETED
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "completed_at"])

        logger.info(
            "[CONVERSATIONS REPORT SERVICE] Conversations report completed %s",
            report.uuid,
        )

    def project_can_receive_new_reports_generation(self, project: Project) -> bool:
        """
        Check if the project can receive new reports generation.
        """
        return not Report.objects.filter(
            project=project,
            source=self.source,
            status__in=[ReportStatus.PENDING, ReportStatus.IN_PROGRESS],
        ).exists()
