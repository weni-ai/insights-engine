import json
import uuid
import zlib
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings

from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.integrations.elasticsearch.tests.mock import (
    MockElasticsearchClient,
)
from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportWorksheet,
)
from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
)
from insights.metrics.conversations.services import (
    BaseConversationsMetricsService,
    ConversationsMetricsService,
)
from insights.projects.models import Project
from insights.reports.choices import ReportFormat, ReportStatus
from insights.reports.models import Report
from insights.sources.dl_events.tests.mock_client import MockDataLakeEventsClient
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.sources.integrations.clients import NexusConversationsAPIClient
from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.users.models import User


class InMemoryCacheClient:
    """Cache client that stores data in memory for testing."""

    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = value
        return True

    def delete(self, key):
        self._store.pop(key, None)
        return True


class TestWorksheetCheckpointing(TestCase):
    def setUp(self):
        self.cache_client = InMemoryCacheClient()
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=MockDataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
                nexus_conversations_client=MagicMock(spec=NexusConversationsAPIClient),
                cache_client=InMemoryCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=self.cache_client,
            nexus_client=MockNexusClient(),
        )
        self.project = Project.objects.create(name="Test Optimized")
        self.user = User.objects.create(email="optimized@test.com", language="en")

    def test_cache_and_load_single_worksheet(self):
        report_uuid = uuid.uuid4()
        worksheet = ConversationsReportWorksheet(
            name="Test Sheet",
            data=[{"URN": "123", "Value": "abc"}],
        )

        self.service._cache_worksheet(report_uuid, "test_section", worksheet)

        loaded = self.service._get_cached_worksheet(report_uuid, "test_section")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Test Sheet")
        self.assertEqual(loaded.data, [{"URN": "123", "Value": "abc"}])

    def test_cache_and_load_worksheet_list(self):
        report_uuid = uuid.uuid4()
        worksheets = [
            ConversationsReportWorksheet(name="Sheet 1", data=[{"a": "1"}]),
            ConversationsReportWorksheet(name="Sheet 2", data=[{"b": "2"}]),
        ]

        self.service._cache_worksheet(report_uuid, "contacts", worksheets)

        loaded = self.service._get_cached_worksheet(report_uuid, "contacts")
        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].name, "Sheet 1")
        self.assertEqual(loaded[1].name, "Sheet 2")

    def test_cache_miss_returns_none(self):
        result = self.service._get_cached_worksheet(uuid.uuid4(), "nonexistent")
        self.assertIsNone(result)

    def test_cached_data_is_compressed(self):
        report_uuid = uuid.uuid4()
        worksheet = ConversationsReportWorksheet(
            name="Compressed", data=[{"key": "value"}]
        )

        self.service._cache_worksheet(report_uuid, "section", worksheet)

        cache_key = self.service._worksheet_cache_key(report_uuid, "section")
        raw = self.cache_client.get(cache_key)

        self.assertIsNotNone(raw)
        decompressed = json.loads(zlib.decompress(raw))
        self.assertEqual(decompressed["name"], "Compressed")

    def test_generate_or_load_uses_cache(self):
        project = self.project
        report = Report.objects.create(
            project=project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        cached_worksheet = ConversationsReportWorksheet(
            name="Cached", data=[{"cached": "true"}]
        )
        self.service._cache_worksheet(report.uuid, "RESOLUTIONS", cached_worksheet)

        generator_fn = MagicMock()

        result = self.service._generate_or_load_worksheet(
            report, "RESOLUTIONS", generator_fn
        )

        generator_fn.assert_not_called()
        self.assertEqual(result.name, "Cached")

    def test_generate_or_load_calls_generator_on_miss(self):
        project = self.project
        report = Report.objects.create(
            project=project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        expected = ConversationsReportWorksheet(
            name="Generated", data=[{"generated": "true"}]
        )
        generator_fn = MagicMock(return_value=expected)

        result = self.service._generate_or_load_worksheet(
            report, "RESOLUTIONS", generator_fn
        )

        generator_fn.assert_called_once()
        self.assertEqual(result.name, "Generated")

        loaded = self.service._get_cached_worksheet(report.uuid, "RESOLUTIONS")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Generated")

    def test_cache_keys_tracked_for_cleanup(self):
        report_uuid = uuid.uuid4()
        worksheet = ConversationsReportWorksheet(
            name="Tracked", data=[{"a": "1"}]
        )

        self.service._cache_worksheet(report_uuid, "section_a", worksheet)
        self.service._cache_worksheet(report_uuid, "section_b", worksheet)

        self.assertIn(str(report_uuid), self.service.cache_keys)
        self.assertEqual(len(self.service.cache_keys[str(report_uuid)]), 2)

        self.service._clear_cache_keys(report_uuid)
        self.assertNotIn(str(report_uuid), self.service.cache_keys)


class TestDatalakeRequestTimeouts(TestCase):
    def setUp(self):
        self.cache_client = InMemoryCacheClient()
        self.mock_dl_client = MockDataLakeEventsClient()
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=self.mock_dl_client,
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
                nexus_conversations_client=MagicMock(spec=NexusConversationsAPIClient),
                cache_client=InMemoryCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=self.cache_client,
            nexus_client=MockNexusClient(),
        )
        self.project = Project.objects.create(name="Test Timeouts")
        self.user = User.objects.create(email="timeout@test.com", language="en")

    @override_settings(REPORT_DATALAKE_REQUEST_TIMEOUT=30)
    def test_sequential_fetch_has_timeout(self):
        """Verify sequential fetch wraps calls with a timeout."""
        call_count = 0
        original_get_events = self.mock_dl_client.get_events

        def get_events_once(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                return []
            return original_get_events(**kwargs)

        self.mock_dl_client.get_events = get_events_once

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        events = self.service.get_datalake_events_sequential(
            report,
            project=str(self.project.uuid),
            date_start="2025-01-01",
            date_end="2025-01-02",
            event_name="weni_nexus_data",
            key="test",
        )

        self.assertIsInstance(events, list)
        self.assertTrue(len(events) > 0)

    @override_settings(REPORT_DATALAKE_REQUEST_TIMEOUT=30)
    def test_parallel_fetch_has_timeout(self):
        """Verify parallel fetch passes timeout to future.result()."""
        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        events = self.service._fetch_pages_in_parallel(
            report,
            total_count=5,
            project=str(self.project.uuid),
            date_start="2025-01-01",
            date_end="2025-01-02",
            event_name="weni_nexus_data",
            key="test",
        )

        self.assertIsInstance(events, list)


class TestStreamedDatalakeEvents(TestCase):
    def setUp(self):
        self.cache_client = InMemoryCacheClient()
        self.mock_dl_client = MockDataLakeEventsClient()
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=100,
            datalake_events_client=self.mock_dl_client,
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
                nexus_conversations_client=MagicMock(spec=NexusConversationsAPIClient),
                cache_client=InMemoryCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=self.cache_client,
            nexus_client=MockNexusClient(),
        )
        self.project = Project.objects.create(name="Test Streamed")
        self.user = User.objects.create(email="stream@test.com", language="en")

    @override_settings(REPORT_DATALAKE_REQUEST_TIMEOUT=30)
    def test_streamed_yields_pages(self):
        """Verify streamed method yields page-by-page."""
        call_count = 0
        original_get_events = self.mock_dl_client.get_events

        def get_events_two_pages(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                return []
            return original_get_events(**kwargs)

        self.mock_dl_client.get_events = get_events_two_pages

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        pages = list(
            self.service.get_datalake_events_streamed(
                report=report,
                project=str(self.project.uuid),
                date_start="2025-01-01",
                date_end="2025-01-02",
                event_name="weni_nexus_data",
                key="test",
            )
        )

        self.assertEqual(len(pages), 2)
        for page in pages:
            self.assertIsInstance(page, list)

    @override_settings(REPORT_DATALAKE_REQUEST_TIMEOUT=30)
    def test_streamed_stops_on_empty_page(self):
        """Verify generator stops when an empty page is returned."""
        empty_client = MagicMock()
        empty_client.get_events.return_value = []
        self.service.datalake_events_client = empty_client

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        pages = list(
            self.service.get_datalake_events_streamed(
                report=report,
                project=str(self.project.uuid),
                date_start="2025-01-01",
                date_end="2025-01-02",
                event_name="weni_nexus_data",
                key="test",
            )
        )

        self.assertEqual(len(pages), 0)


class TestParallelWorksheetGeneration(TestCase):
    def setUp(self):
        self.cache_client = InMemoryCacheClient()
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=MockDataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
                nexus_conversations_client=MagicMock(spec=NexusConversationsAPIClient),
                cache_client=InMemoryCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=self.cache_client,
            nexus_client=MockNexusClient(),
        )
        self.project = Project.objects.create(name="Test Parallel")
        self.user = User.objects.create(email="parallel@test.com", language="en")

    def test_build_worksheet_specs_filters_by_sections(self):
        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["CSAT_AI", "NPS_AI"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        specs = self.service._build_worksheet_specs(
            report=report,
            sections=["CSAT_AI", "NPS_AI"],
            source_config=report.source_config,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 2),
            shared_classification_events=None,
        )

        section_keys = [s[0] for s in specs]
        self.assertEqual(section_keys, ["CSAT_AI", "NPS_AI"])

    def test_build_worksheet_specs_excludes_unlisted_sections(self):
        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["CSAT_AI"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        specs = self.service._build_worksheet_specs(
            report=report,
            sections=["CSAT_AI"],
            source_config=report.source_config,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 2),
            shared_classification_events=None,
        )

        section_keys = [s[0] for s in specs]
        self.assertIn("CSAT_AI", section_keys)
        self.assertNotIn("RESOLUTIONS", section_keys)
        self.assertNotIn("TOPICS_AI", section_keys)

    def test_build_worksheet_specs_empty_sections(self):
        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": []},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        specs = self.service._build_worksheet_specs(
            report=report,
            sections=[],
            source_config=report.source_config,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 2),
            shared_classification_events=None,
        )

        self.assertEqual(specs, [])


class TestFeatureFlagGating(TestCase):
    def setUp(self):
        self.cache_client = InMemoryCacheClient()
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=MockDataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
                nexus_conversations_client=MagicMock(spec=NexusConversationsAPIClient),
                cache_client=InMemoryCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=self.cache_client,
            nexus_client=MockNexusClient(),
        )
        self.project = Project.objects.create(name="Test FF")
        self.user = User.objects.create(email="ff@test.com", language="en")

    @patch(
        "insights.metrics.conversations.reports.services.is_feature_active_for_attributes"
    )
    def test_optimized_generation_disabled_by_default(self, mock_ff):
        mock_ff.return_value = False

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        result = self.service._is_optimized_generation_enabled(report)
        self.assertFalse(result)

    @patch(
        "insights.metrics.conversations.reports.services.is_feature_active_for_attributes"
    )
    def test_optimized_generation_enabled(self, mock_ff):
        mock_ff.return_value = True

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        result = self.service._is_optimized_generation_enabled(report)
        self.assertTrue(result)

    @patch(
        "insights.metrics.conversations.reports.services.is_feature_active_for_attributes"
    )
    def test_optimized_generation_defaults_false_on_error(self, mock_ff):
        mock_ff.side_effect = Exception("GrowthBook unavailable")

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        result = self.service._is_optimized_generation_enabled(report)
        self.assertFalse(result)

    @patch(
        "insights.metrics.conversations.reports.services.is_feature_active_for_attributes"
    )
    def test_optimized_generation_passes_correct_attributes(self, mock_ff):
        mock_ff.return_value = False

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service._is_optimized_generation_enabled(report)

        call_args = mock_ff.call_args
        self.assertEqual(
            call_args[0][0],
            settings.CONVERSATIONS_REPORT_OPTIMIZED_GENERATION_FEATURE_FLAG_KEY,
        )
        attributes = call_args[1]["attributes"]
        self.assertEqual(attributes["projectUUID"], str(self.project.uuid))
        self.assertEqual(attributes["userEmail"], "ff@test.com")

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._get_worksheets_optimized"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._get_worksheets"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._is_optimized_generation_enabled"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
    )
    def test_generate_uses_optimized_path_when_enabled(
        self, mock_send_email, mock_ff, mock_get_worksheets, mock_get_optimized
    ):
        mock_ff.return_value = True
        mock_get_optimized.return_value = []
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={
                "start": "2025-01-01T00:00:00+00:00",
                "end": "2025-01-02T00:00:00+00:00",
            },
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        self.service.generate(report)

        mock_get_optimized.assert_called_once()
        mock_get_worksheets.assert_not_called()

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._get_worksheets_optimized"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._get_worksheets"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService._is_optimized_generation_enabled"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
    )
    def test_generate_uses_legacy_path_when_disabled(
        self, mock_send_email, mock_ff, mock_get_worksheets, mock_get_optimized
    ):
        mock_ff.return_value = False
        mock_get_worksheets.return_value = []
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={
                "start": "2025-01-01T00:00:00+00:00",
                "end": "2025-01-02T00:00:00+00:00",
            },
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        self.service.generate(report)

        mock_get_worksheets.assert_called_once()
        mock_get_optimized.assert_not_called()


class TestCeleryTaskTimeLimits(TestCase):
    def test_task_has_soft_time_limit(self):
        from insights.metrics.conversations.tasks import (
            generate_conversations_report,
        )

        self.assertEqual(
            generate_conversations_report.soft_time_limit,
            settings.REPORT_GENERATION_SOFT_TIME_LIMIT,
        )

    def test_task_has_hard_time_limit(self):
        from insights.metrics.conversations.tasks import (
            generate_conversations_report,
        )

        self.assertEqual(
            generate_conversations_report.time_limit,
            settings.REPORT_GENERATION_HARD_TIME_LIMIT,
        )

    @patch(
        "insights.metrics.conversations.tasks.ConversationsReportService"
    )
    def test_soft_time_limit_marks_report_interrupted(self, mock_service_cls):
        from celery.exceptions import SoftTimeLimitExceeded
        from insights.metrics.conversations.tasks import (
            generate_conversations_report,
        )

        project = Project.objects.create(name="Test Celery")
        user = User.objects.create(email="celery@test.com", language="en")

        report = Report.objects.create(
            project=project,
            source="conversations_dashboard",
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=user,
            status=ReportStatus.PENDING,
        )

        mock_service_instance = MagicMock()
        mock_service_instance.generate.side_effect = SoftTimeLimitExceeded()
        mock_service_cls.return_value = mock_service_instance

        generate_conversations_report()

        report.refresh_from_db()
        config = report.config or {}
        self.assertTrue(config.get("interrupted"))
        self.assertIsNotNone(config.get("interrupted_at"))
