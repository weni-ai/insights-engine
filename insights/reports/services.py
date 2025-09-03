from abc import ABC, abstractmethod

from insights.reports.models import Report
from insights.reports.choices import ReportSource, ReportFormat, ReportStatus

from insights.users.models import User


class BaseReportService(ABC):
    """
    Base class for report services.
    """


class ReportService(BaseReportService):
    """
    Service to generate reports.
    """

    def request_generation(
        self,
        source: ReportSource,
        source_config: dict,
        filters: dict,
        format: ReportFormat,
        requested_by: User,
    ) -> Report:
        """
        Request the generation of a report.
        """
        report = Report.objects.create(
            source=source,
            source_config=source_config,
            filters=filters,
            format=format,
            requested_by=requested_by,
            status=ReportStatus.PENDING,
        )

        return report
