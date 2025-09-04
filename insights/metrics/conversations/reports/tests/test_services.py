from unittest.mock import patch

from django.test import TestCase

from insights.users.models import User
from insights.reports.models import Report
from insights.reports.choices import ReportFormat, ReportStatus
from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
)
from insights.projects.models import Project


class TestConversationsReportService(TestCase):
    def setUp(self):
        self.service = ConversationsReportService()
        self.project = Project.objects.create(name="Test")
        self.user = User.objects.create(
            email="test@test.com",
            language="en",
        )

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email(self, mock_send_email):
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.send_email(report, "test")

        mock_send_email.assert_called_once_with(
            fail_silently=False,
        )

    def test_cannot_request_generation_without_source_config(self):
        with self.assertRaises(ValueError) as context:
            self.service.request_generation(
                project=self.project,
                source_config={},
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                report_format=ReportFormat.CSV,
                requested_by=self.user,
            )

        self.assertEqual(
            str(context.exception),
            "source_config cannot be empty when requesting generation of conversations report",
        )

    def test_cannot_request_generation_without_filters(self):
        with self.assertRaises(ValueError) as context:
            self.service.request_generation(
                project=self.project,
                source_config={"sections": ["RESOLUTIONS"]},
                filters={},
                report_format=ReportFormat.CSV,
                requested_by=self.user,
            )

        self.assertEqual(
            str(context.exception),
            "filters cannot be empty when requesting generation of conversations report",
        )

    def test_cannot_request_generation_without_sections_in_source_config(self):
        with self.assertRaises(ValueError) as context:
            self.service.request_generation(
                project=self.project,
                source_config={"sections": []},
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                report_format=ReportFormat.CSV,
                requested_by=self.user,
            )

        self.assertEqual(
            str(context.exception),
            "sections cannot be empty when requesting generation of conversations report",
        )

    def test_request_generation(self):
        report = self.service.request_generation(
            project=self.project,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            report_format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.assertIsInstance(report, Report)
        self.assertEqual(report.project, self.project)
        self.assertEqual(report.source, self.service.source)
        self.assertEqual(report.source_config, {"sections": ["RESOLUTIONS"]})
        self.assertEqual(report.filters, {"start": "2025-01-01", "end": "2025-01-02"})
        self.assertEqual(report.format, ReportFormat.CSV)
        self.assertEqual(report.requested_by, self.user)
        self.assertEqual(report.status, ReportStatus.PENDING)

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.process_csv"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
    )
    def test_generate(self, mock_send_email, mock_process_csv):
        mock_process_csv.return_value = None
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.generate(report)

        mock_process_csv.assert_called_once_with(report)
        mock_send_email.assert_called_once()

    def test_project_can_receive_new_reports_generation_when_no_reports_exist(self):
        self.assertTrue(
            self.service.project_can_receive_new_reports_generation(self.project)
        )

    def test_project_can_receive_new_reports_generation_when_pending_report_exists(
        self,
    ):
        Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        self.assertFalse(
            self.service.project_can_receive_new_reports_generation(self.project)
        )

    def test_project_can_receive_new_reports_generation_when_in_progress_report_exists(
        self,
    ):
        Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        self.assertFalse(
            self.service.project_can_receive_new_reports_generation(self.project)
        )

    def test_project_cannot_receive_new_reports_generation_when_ready_report_exists(
        self,
    ):
        Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.READY,
        )

        self.assertTrue(
            self.service.project_can_receive_new_reports_generation(self.project)
        )
