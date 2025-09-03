from abc import ABC, abstractmethod
import logging

from insights.reports.models import Report
from insights.reports.choices import ReportSource, ReportFormat, ReportStatus

from insights.users.models import User
from insights.projects.models import Project

logger = logging.getLogger(__name__)


class BaseSourceReportService(ABC):
    """
    Base class for source report services.
    """

    @abstractmethod
    def start_generation(self, report: Report) -> None:
        """
        Start the generation of a report.
        """
        raise NotImplementedError("Subclasses must implement this method")


class BaseReportService(ABC):
    """
    Base class for report services.
    """

    @abstractmethod
    def request_generation(
        self,
        project: Project,
        source: ReportSource,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> Report:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_source_report_service(
        self, source: ReportSource
    ) -> BaseSourceReportService:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def start_generation(self, report: Report) -> None:
        raise NotImplementedError("Subclasses must implement this method")


class ReportService(BaseReportService):
    """
    Service to generate reports.
    """

    def request_generation(
        self,
        project: Project,
        source: ReportSource,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> Report:
        """
        Request the generation of a report.
        """
        logger.info(
            "[REPORT SERVICE] Requesting generation of report for source %s by user %s",
            source,
            requested_by.email,
        )

        report = Report.objects.create(
            source=source,
            source_config=source_config,
            filters=filters,
            format=report_format,
            requested_by=requested_by,
            status=ReportStatus.PENDING,
            project=project,
        )

        logger.info(
            "[REPORT SERVICE] Report created with uuid %s, requested by %s",
            report.uuid,
            requested_by.email,
        )

        return report

    def get_source_report_service(
        self, source: ReportSource
    ) -> BaseSourceReportService:
        """
        Get the source report service.
        """
        from insights.reports.factories import SourceReportServiceFactory

        return SourceReportServiceFactory.get_service(source)

    def start_generation(self, report: Report) -> None:
        """
        Start the generation of a report.
        """
        service = self.get_source_report_service(report.source)
        service.start_generation(report)
