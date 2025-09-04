from unittest.mock import MagicMock

from insights.metrics.conversations.reports.services import (
    BaseConversationsReportService,
)
from insights.reports.choices import ReportSource
from insights.reports.models import Report
from insights.projects.models import Project
from insights.users.models import User
from insights.reports.choices import ReportFormat


class MockConversationsReportService(BaseConversationsReportService):
    def process_csv(self, report: Report) -> None:
        pass

    def process_xlsx(self, report: Report) -> None:
        pass

    def send_email(self, report: Report, file_content: str) -> None:
        pass

    def request_generation(
        self,
        project: Project,
        source_config: dict,
        filters: dict,
        report_format: ReportFormat,
        requested_by: User,
    ) -> None:
        pass

    def generate(self, report: Report) -> None:
        pass

    def get_current_report_for_project(self, project: Project) -> bool:
        pass

    def get_next_report_to_generate(self) -> Report | None:
        pass

    def __init__(self):
        self.source = ReportSource.CONVERSATIONS_DASHBOARD
        self.process_csv = MagicMock()
        self.process_xlsx = MagicMock()
        self.send_email = MagicMock()
        self.request_generation = MagicMock()
        self.generate = MagicMock()
        self.get_next_report_to_generate = MagicMock()
        self.project_can_receive_new_reports_generation = MagicMock()
