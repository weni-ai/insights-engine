from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase, override_settings
from django.utils import timezone

from insights.metrics.conversations.tasks import (
    check_project_sales_funnel_on_datalake,
    generate_conversations_report,
    timeout_reports,
)
from insights.projects.models import Project
from insights.reports.choices import ReportStatus
from insights.reports.models import Report


class TestGenerateConversationsReport(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    @override_settings(
        HOSTNAME="host-1",
        REPORT_GENERATION_MAX_CONCURRENT_REPORTS=2,
    )
    def test_returns_early_when_max_concurrent_reports_reached(self):
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.IN_PROGRESS,
        )
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.IN_PROGRESS,
        )

        result = generate_conversations_report()

        self.assertIsNone(result)

    @override_settings(
        HOSTNAME="host-2",
        REPORT_GENERATION_MAX_CONCURRENT_REPORTS=5,
        CONVERSATIONS_REPORT_EVENTS_LIMIT_PER_PAGE=100,
        CONVERSATIONS_REPORT_PAGE_LIMIT=10,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_SIZE=100,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_LIMIT=10,
    )
    @patch("insights.metrics.conversations.tasks.ConversationsReportService")
    @patch("insights.metrics.conversations.tasks.ElasticsearchClient")
    @patch("insights.metrics.conversations.tasks.DataLakeEventsClient")
    @patch("insights.metrics.conversations.tasks.CacheClient")
    def test_picks_interrupted_report_from_another_host(
        self,
        mock_cache_client,
        mock_datalake_client,
        mock_es_client,
        mock_report_service_cls,
    ):
        interrupted_report = Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.IN_PROGRESS,
            config={
                "interrupted": True,
                "interrupted_on_host": "host-1",
                "interrupted_at": "2024-01-01T00:00:00Z",
            },
        )

        mock_service_instance = MagicMock()
        mock_report_service_cls.return_value = mock_service_instance

        generate_conversations_report()

        mock_service_instance.generate.assert_called_once()
        call_arg = mock_service_instance.generate.call_args[0][0]
        self.assertEqual(call_arg.uuid, interrupted_report.uuid)

        interrupted_report.refresh_from_db()
        self.assertFalse(interrupted_report.config["interrupted"])
        self.assertEqual(interrupted_report.config["task_host"], "host-2")

    @override_settings(
        HOSTNAME="host-1",
        REPORT_GENERATION_MAX_CONCURRENT_REPORTS=5,
        CONVERSATIONS_REPORT_EVENTS_LIMIT_PER_PAGE=100,
        CONVERSATIONS_REPORT_PAGE_LIMIT=10,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_SIZE=100,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_LIMIT=10,
    )
    @patch("insights.metrics.conversations.tasks.ConversationsReportService")
    @patch("insights.metrics.conversations.tasks.ElasticsearchClient")
    @patch("insights.metrics.conversations.tasks.DataLakeEventsClient")
    @patch("insights.metrics.conversations.tasks.CacheClient")
    def test_generates_oldest_pending_report(
        self,
        mock_cache_client,
        mock_datalake_client,
        mock_es_client,
        mock_report_service_cls,
    ):
        older_report = Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.PENDING,
        )
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.PENDING,
        )

        mock_service_instance = MagicMock()
        mock_report_service_cls.return_value = mock_service_instance

        generate_conversations_report()

        mock_service_instance.generate.assert_called_once()
        call_arg = mock_service_instance.generate.call_args[0][0]
        self.assertEqual(call_arg.uuid, older_report.uuid)

    @override_settings(
        HOSTNAME="host-1",
        REPORT_GENERATION_MAX_CONCURRENT_REPORTS=5,
    )
    def test_returns_early_when_no_pending_reports(self):
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.READY,
        )

        result = generate_conversations_report()

        self.assertIsNone(result)

    @override_settings(
        HOSTNAME="host-1",
        REPORT_GENERATION_MAX_CONCURRENT_REPORTS=5,
        CONVERSATIONS_REPORT_EVENTS_LIMIT_PER_PAGE=100,
        CONVERSATIONS_REPORT_PAGE_LIMIT=10,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_SIZE=100,
        CONVERSATIONS_REPORT_ELASTIC_PAGE_LIMIT=10,
    )
    @patch("insights.metrics.conversations.tasks.ConversationsReportService")
    @patch("insights.metrics.conversations.tasks.ElasticsearchClient")
    @patch("insights.metrics.conversations.tasks.DataLakeEventsClient")
    @patch("insights.metrics.conversations.tasks.CacheClient")
    def test_exception_during_generate_is_logged_not_raised(
        self,
        mock_cache_client,
        mock_datalake_client,
        mock_es_client,
        mock_report_service_cls,
    ):
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.PENDING,
        )

        mock_service_instance = MagicMock()
        mock_service_instance.generate.side_effect = Exception("Something broke")
        mock_report_service_cls.return_value = mock_service_instance

        generate_conversations_report()


class TestTimeoutReports(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    @override_settings(REPORT_GENERATION_TIMEOUT=3600)
    def test_marks_timed_out_reports_as_failed(self):
        timed_out_report = Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.IN_PROGRESS,
            started_at=timezone.now() - timedelta(seconds=7200),
        )

        timeout_reports()

        timed_out_report.refresh_from_db()
        self.assertEqual(timed_out_report.status, ReportStatus.FAILED)
        self.assertIsNotNone(timed_out_report.completed_at)
        self.assertEqual(
            timed_out_report.errors, {"timeout": "Report generation timed out"}
        )

    @override_settings(REPORT_GENERATION_TIMEOUT=3600)
    def test_returns_early_when_no_in_progress_reports(self):
        Report.objects.create(
            project=self.project,
            source="CONVERSATIONS_DASHBOARD",
            format="CSV",
            status=ReportStatus.PENDING,
            started_at=timezone.now() - timedelta(seconds=7200),
        )

        result = timeout_reports()

        self.assertIsNone(result)


class TestCheckProjectSalesFunnelOnDatalake(TestCase):
    @patch(
        "insights.metrics.conversations.tasks.CheckProjectSalesFunnelOnDatalakeUseCase"
    )
    @patch("insights.metrics.conversations.tasks.DatalakeConversationsMetricsService")
    def test_executes_use_case_with_project_uuid(
        self,
        mock_datalake_service_cls,
        mock_use_case_cls,
    ):
        project_uuid = uuid4()
        mock_datalake_service = MagicMock()
        mock_datalake_service_cls.return_value = mock_datalake_service

        mock_use_case_instance = MagicMock()
        mock_use_case_cls.return_value = mock_use_case_instance

        check_project_sales_funnel_on_datalake(project_uuid)

        mock_use_case_cls.assert_called_once_with(mock_datalake_service)
        mock_use_case_instance.execute.assert_called_once_with(project_uuid)
