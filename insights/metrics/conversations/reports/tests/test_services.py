from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportWorksheet,
)
from insights.sources.dl_events.tests.mock_client import (
    ClassificationMockDataLakeEventsClient,
)
from insights.users.models import User
from insights.reports.models import Report
from insights.reports.choices import ReportFormat, ReportStatus
from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
)
from insights.projects.models import Project


class TestConversationsReportService(TestCase):
    def setUp(self):
        self.service = ConversationsReportService(
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=ClassificationMockDataLakeEventsClient(),
        )
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

    def test_cannot_request_generation_without_sections_or_custom_widgets_in_source_config(
        self,
    ):
        with self.assertRaises(ValueError) as context:
            self.service.request_generation(
                project=self.project,
                source_config={"sections": [], "custom_widgets": []},
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                report_format=ReportFormat.CSV,
                requested_by=self.user,
            )

        self.assertEqual(
            str(context.exception),
            "sections or custom_widgets cannot be empty when requesting generation of conversations report",
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
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_resolutions_worksheet"
    )
    def test_generate(
        self, mock_get_resolutions_worksheet, mock_send_email, mock_process_csv
    ):
        mock_process_csv.return_value = None
        mock_send_email.return_value = None
        mock_get_resolutions_worksheet.return_value = ConversationsReportWorksheet(
            name="Resolutions",
            data=[{"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}],
        )

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.generate(report)

        mock_process_csv.assert_called_once_with(
            report,
            [
                ConversationsReportWorksheet(
                    name="Resolutions",
                    data=[
                        {"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}
                    ],
                )
            ],
        )
        mock_send_email.assert_called_once()

    def test_get_current_report_for_project_when_no_reports_exist(self):
        self.assertIsNone(self.service.get_current_report_for_project(self.project))

    def test_get_current_report_for_project_when_pending_report_exists(
        self,
    ):
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        result = self.service.get_current_report_for_project(self.project)

        self.assertEqual(result, report)

    def test_get_current_report_for_project_when_in_progress_report_exists(
        self,
    ):
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        result = self.service.get_current_report_for_project(self.project)

        self.assertEqual(result, report)

    def test_get_current_report_for_project_when_ready_report_exists(
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

        result = self.service.get_current_report_for_project(self.project)

        self.assertIsNone(result)

    def test_get_next_report_to_generate_when_no_reports_exist(self):
        self.assertIsNone(self.service.get_next_report_to_generate())

    def test_get_next_report_to_generate_when_pending_report_exists(self):
        def create_report(created_on):
            with patch("django.utils.timezone.now") as mock_now:
                mock_now.return_value = created_on

                return Report.objects.create(
                    project=self.project,
                    source=self.service.source,
                    source_config={"sections": ["RESOLUTIONS"]},
                    filters={"start": "2025-01-01", "end": "2025-01-02"},
                    format=ReportFormat.CSV,
                    requested_by=self.user,
                    status=ReportStatus.PENDING,
                )

        first_report = create_report(timezone.now() - timedelta(hours=1))
        second_report = create_report(timezone.now() - timedelta(hours=2))

        self.assertEqual(self.service.get_next_report_to_generate(), second_report)

        second_report.status = ReportStatus.IN_PROGRESS
        second_report.save(update_fields=["status"])

        self.assertEqual(self.service.get_next_report_to_generate(), first_report)

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_when_no_events_exist(self, mock_get_datalake_events):
        mock_get_datalake_events.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        events = self.service.get_datalake_events(report)

        self.assertEqual(events, [])

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_when_events_exist(self, mock_get_datalake_events):
        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if kwargs.get("offset") == 0:
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        events = self.service.get_datalake_events(report)

        self.assertEqual(events, mock_events)

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_when_events_exist_with_multiple_pages(
        self, mock_get_datalake_events
    ):
        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if kwargs.get("offset") < self.service.events_limit_per_page * 2:
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        events = self.service.get_datalake_events(report)

        self.assertEqual(events, mock_events * 2)

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_when_page_limit_is_reached(
        self, mock_get_datalake_events
    ):
        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if (
                kwargs.get("offset")
                < self.service.events_limit_per_page * self.service.page_limit + 1
            ):
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_datalake_events(report)

        self.assertEqual(
            str(context.exception),
            "Report has more than 5 pages",
        )

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_when_report_is_failed(self, mock_get_datalake_events):
        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if (
                kwargs.get("offset")
                < self.service.events_limit_per_page * self.service.page_limit + 1
            ):
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.FAILED,
            errors={"send_email": "test", "event_id": "test"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_datalake_events(report)

        self.assertEqual(
            str(context.exception),
            "Report %s is not in progress" % report.uuid,
        )
