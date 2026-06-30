from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from insights.metrics.conversations.tasks import timeout_reports
from insights.projects.models import Project
from insights.reports.choices import ReportFormat, ReportSource, ReportStatus
from insights.reports.models import Report
from insights.users.models import User


@override_settings(REPORT_GENERATION_TIMEOUT=3600)
class TestTimeoutReports(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create(email="test@test.com", language="en")

    def test_timeout_reports_does_nothing_when_no_stale_reports(self):
        Report.objects.create(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
            started_at=timezone.now(),
        )

        with patch(
            "insights.metrics.conversations.tasks._create_conversations_report_service"
        ) as mock_create_service:
            timeout_reports()

            mock_create_service.assert_not_called()

    @patch(
        "insights.metrics.conversations.tasks._create_conversations_report_service"
    )
    def test_timeout_reports_marks_reports_as_failed_and_sends_email(
        self, mock_create_service
    ):
        mock_service = mock_create_service.return_value

        report = Report.objects.create(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
            started_at=timezone.now() - timedelta(hours=2),
        )

        timeout_reports()

        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.FAILED)
        self.assertIsNotNone(report.completed_at)
        self.assertEqual(report.errors, {"timeout": "Report generation timed out"})
        mock_service.send_email.assert_called_once_with(report, [], is_error=True)
