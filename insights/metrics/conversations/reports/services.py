from insights.reports.services import BaseSourceReportService


from insights.reports.models import Report


class ConversationsReportService(BaseSourceReportService):
    """
    Service to generate conversations reports.
    """

    def start_generation(self, report: Report) -> None:
        """
        Start the generation of a conversations report.
        """
        pass
