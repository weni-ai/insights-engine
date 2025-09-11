from insights.reports.services import BaseSourceReportService
from insights.reports.choices import ReportSource

from insights.metrics.conversations.reports.services import ConversationsReportService


SERVICE_FACTORY_MAP = {
    ReportSource.CONVERSATIONS_DASHBOARD: ConversationsReportService,
}


class SourceReportServiceFactory:
    """
    Factory to get the source report service.
    """

    def get_service(self, source: ReportSource) -> BaseSourceReportService:
        if source not in SERVICE_FACTORY_MAP:
            raise ValueError(f"Source {source} not supported")

        return SERVICE_FACTORY_MAP[source]()
