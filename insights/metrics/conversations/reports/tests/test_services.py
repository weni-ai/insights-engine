from datetime import datetime
import json
from unittest.mock import patch
import uuid

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportWorksheet,
    ConversationsReportFile,
)
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.integrations.elasticsearch.tests.mock import (
    MockElasticsearchClient,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.sources.dl_events.tests.mock_client import (
    ClassificationMockDataLakeEventsClient,
)
from insights.users.models import User
from insights.reports.models import Report
from insights.reports.choices import ReportFormat, ReportStatus
from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
    serialize_filters_for_json,
)
from insights.projects.models import Project
from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.sources.tests.mock import MockCacheClient
from insights.widgets.models import Widget
from insights.dashboards.models import Dashboard


class TestConversationsReportService(TestCase):
    def setUp(self):
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=ClassificationMockDataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(
                datalake_service=MockDatalakeConversationsMetricsService(),
                nexus_client=MockNexusClient(),
                cache_client=MockCacheClient(),
                flowruns_query_executor=MockFlowRunsQueryExecutor(),
            ),
            cache_client=MockCacheClient(),
        )
        self.project = Project.objects.create(name="Test")
        self.dashboard = Dashboard.objects.create(name="Test", project=self.project)
        self.user = User.objects.create(
            email="test@test.com",
            language="en",
        )

    def test_ensure_unique_worksheet_name(self):
        used_names = set()
        self.assertEqual(
            self.service._ensure_unique_worksheet_name("Test", used_names), "Test"
        )
        self.assertEqual(
            self.service._ensure_unique_worksheet_name("Test", used_names), "Test (1)"
        )
        self.assertEqual(
            self.service._ensure_unique_worksheet_name("Test", used_names), "Test (2)"
        )
        self.assertEqual(
            self.service._ensure_unique_worksheet_name("Test (1)", used_names),
            "Test (1) (1)",
        )

    def test_add_cache_key(self):
        report_uuid = uuid.uuid4()
        cache_key = "test_cache_key"

        self.assertEqual(self.service.cache_keys, {})

        self.service._add_cache_key(report_uuid, cache_key)

        self.assertIn(str(report_uuid), self.service.cache_keys)
        self.assertEqual(self.service.cache_keys, {str(report_uuid): {cache_key}})

    def test_clear_cache_keys(self):
        report_uuid = uuid.uuid4()
        cache_key = "test_cache_key"

        self.service._add_cache_key(report_uuid, cache_key)
        self.assertIn(str(report_uuid), self.service.cache_keys)
        self.assertEqual(self.service.cache_keys[str(report_uuid)], {cache_key})

        self.service._clear_cache_keys(report_uuid)
        self.assertNotIn(str(report_uuid), self.service.cache_keys)
        self.assertEqual(self.service.cache_keys, {})

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

        self.service.send_email(
            report, [ConversationsReportFile(name="test", content="test")]
        )

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
        "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_resolutions_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_transferred_to_human_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_topics_distribution_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_csat_ai_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_nps_ai_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_csat_human_worksheet"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_nps_human_worksheet"
    )
    def test_generate(
        self,
        mock_get_nps_human_worksheet,
        mock_get_csat_human_worksheet,
        mock_get_nps_ai_worksheet,
        mock_get_csat_ai_worksheet,
        mock_get_topics_distribution_worksheet,
        mock_get_transferred_to_human_worksheet,
        mock_get_resolutions_worksheet,
        mock_send_email,
    ):
        mock_send_email.return_value = None
        mock_get_resolutions_worksheet.return_value = ConversationsReportWorksheet(
            name="Resolutions",
            data=[{"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}],
        )
        mock_get_transferred_to_human_worksheet.return_value = (
            ConversationsReportWorksheet(
                name="Transferred to Human",
                data=[
                    {"URN": "123", "Transferred to Human": "Yes", "Date": "2025-01-01"}
                ],
            )
        )
        mock_get_topics_distribution_worksheet.return_value = (
            ConversationsReportWorksheet(
                name="Test",
                data=[
                    {
                        "URN": "1",
                        "Topic": "Test",
                        "Subtopic": "Test",
                        "Date": "2025-01-01T00:00:00.000000Z",
                    }
                ],
            )
        )
        mock_get_csat_ai_worksheet.return_value = ConversationsReportWorksheet(
            name="CSAT AI",
            data=[
                {
                    "URN": "123",
                    "Date": "14/09/2025 19:27:10",
                    "Score": "5",
                }
            ],
        )
        mock_get_nps_ai_worksheet.return_value = ConversationsReportWorksheet(
            name="NPS AI",
            data=[
                {
                    "URN": "123",
                    "Date": "14/09/2025 19:27:10",
                    "Score": "5",
                }
            ],
        )
        mock_get_csat_human_worksheet.return_value = ConversationsReportWorksheet(
            name="CSAT Human",
            data=[
                {
                    "Date": "2025-01-01 00:00:00",
                    "Score": "5",
                    "URN": "1234567890",
                },
            ],
        )

        mock_get_nps_human_worksheet.return_value = ConversationsReportWorksheet(
            name="NPS Human",
            data=[
                {
                    "Date": "2025-01-01 00:00:00",
                    "Score": "5",
                    "URN": "1234567890",
                },
            ],
        )

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={
                "sections": [
                    "RESOLUTIONS",
                    "TRANSFERRED",
                    "TOPICS_AI",
                    "TOPICS_HUMAN",
                    "CSAT_AI",
                    "NPS_AI",
                    "CSAT_HUMAN",
                    "NPS_HUMAN",
                ],
                "csat_human_flow_uuid": str(uuid.uuid4()),
                "csat_human_op_field": "op_field",
                "nps_human_flow_uuid": str(uuid.uuid4()),
                "nps_human_op_field": "op_field",
            },
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.generate(report)
        mock_send_email.assert_called_once()
        mock_get_csat_human_worksheet.assert_called_once()
        mock_get_nps_human_worksheet.assert_called_once()

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
    @patch("insights.sources.tests.mock.MockCacheClient.set")
    @patch("insights.sources.tests.mock.MockCacheClient.get")
    def test_get_datalake_events_when_no_events_exist(
        self, mock_cache_get, mock_cache_set, mock_get_datalake_events
    ):
        mock_get_datalake_events.return_value = []
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS", "TRANSFERRED"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        kwargs = {"key": "example"}

        events = self.service.get_datalake_events(report, **kwargs)

        self.assertEqual(events, [])

        cache_key = (
            f"datalake_events:{report.uuid}:{json.dumps(kwargs, sort_keys=True)}"
        )

        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once_with(
            cache_key, json.dumps(events), ex=settings.REPORT_GENERATION_TIMEOUT
        )

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    @patch("insights.sources.tests.mock.MockCacheClient.set")
    @patch("insights.sources.tests.mock.MockCacheClient.get")
    def test_get_datalake_events_when_events_exist(
        self, mock_cache_get, mock_cache_set, mock_get_datalake_events
    ):
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None

        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if kwargs.get("offset") == 0:
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS", "TRANSFERRED"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        kwargs = {"key": "example"}

        events = self.service.get_datalake_events(report, **kwargs)

        self.assertEqual(events, mock_events)

        cache_key = (
            f"datalake_events:{report.uuid}:{json.dumps(kwargs, sort_keys=True)}"
        )

        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once_with(
            cache_key, json.dumps(events), ex=settings.REPORT_GENERATION_TIMEOUT
        )

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    @patch("insights.sources.tests.mock.MockCacheClient.set")
    @patch("insights.sources.tests.mock.MockCacheClient.get")
    def test_get_datalake_events_when_events_exist_with_multiple_pages(
        self, mock_cache_get, mock_cache_set, mock_get_datalake_events
    ):
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None

        mock_events = [{"id": "1"}, {"id": "2"}]

        def get_datalake_events(**kwargs):
            if kwargs.get("offset") < self.service.events_limit_per_page * 2:
                return mock_events
            return []

        mock_get_datalake_events.side_effect = get_datalake_events

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS", "TRANSFERRED"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        kwargs = {"key": "example"}

        events = self.service.get_datalake_events(report, **kwargs)

        self.assertEqual(events, mock_events * 2)

        cache_key = (
            f"datalake_events:{report.uuid}:{json.dumps(kwargs, sort_keys=True)}"
        )

        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once_with(
            cache_key, json.dumps(events), ex=settings.REPORT_GENERATION_TIMEOUT
        )

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
            source_config={"sections": ["RESOLUTIONS", "TRANSFERRED"]},
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
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
    )
    def test_get_topics_distribution_worksheet_for_ai(
        self, mock_get_topics, mock_get_datalake_events
    ):
        nexus_topics_data = {
            "name": "Test Topic",
            "uuid": uuid.uuid4(),
            "subtopic": [
                {
                    "name": "Test Subtopic",
                    "uuid": uuid.uuid4(),
                }
            ],
        }

        mock_get_topics.return_value = [nexus_topics_data]

        mock_get_datalake_events.return_value = [
            {
                "contact_urn": "1",
                "date": "2025-01-01T00:00:00.000000Z",
                "metadata": json.dumps(
                    {
                        "topic_uuid": str(nexus_topics_data["uuid"]),
                        "subtopic_uuid": str(nexus_topics_data["subtopic"][0]["uuid"]),
                        "subtopic": nexus_topics_data["subtopic"][0]["name"],
                    }
                ),
                "value": nexus_topics_data["name"],
            },
            {
                "contact_urn": "2",
                "date": "2025-01-01T00:00:00.000000Z",
                "metadata": json.dumps(
                    {
                        "topic_uuid": str(uuid.uuid4()),
                        "subtopic_uuid": str(uuid.uuid4()),
                        "subtopic": "Test Subtopic 2",
                    }
                ),
                "value": "Test Topic 2",
            },
        ]

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["TOPICS_AI"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            requested_by=self.user,
        )

        worksheet = self.service.get_topics_distribution_worksheet(
            report,
            datetime(2025, 1, 1),
            datetime(2025, 1, 2),
            ConversationType.AI,
        )

        self.assertIsInstance(worksheet, ConversationsReportWorksheet)
        self.assertEqual(len(worksheet.data), 2)
        self.assertEqual(worksheet.data[0]["Topic"], "Test Topic")
        self.assertEqual(worksheet.data[0]["Subtopic"], "Test Subtopic")
        self.assertEqual(worksheet.data[1]["Topic"], "Unclassified")
        self.assertEqual(worksheet.data[1]["Subtopic"], "Unclassified")

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
            source_config={"sections": ["RESOLUTIONS", "TRANSFERRED"]},
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

    @patch("insights.sources.tests.mock.MockCacheClient.set")
    @patch("insights.sources.tests.mock.MockCacheClient.get")
    def test_get_flowsrun_results_by_contacts(self, mock_cache_get, mock_cache_set):
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None

        def get_side_effect(*args, **kwargs):
            # First call: return hits
            if not hasattr(get_side_effect, "called"):
                get_side_effect.called = True

                return {
                    "hits": {
                        "total": {"value": 10},
                        "hits": [
                            {
                                "_source": {
                                    "project_uuid": uuid.uuid4(),
                                    "contact_uuid": uuid.uuid4(),
                                    "created_on": "2025-01-01",
                                    "modified_on": "2025-01-01",
                                    "contact_name": "John Doe",
                                    "contact_urn": "1234567890",
                                    "values": [
                                        {
                                            "name": "user_feedback",
                                            "value": "5",
                                        }
                                    ],
                                }
                            }
                        ],
                    }
                }

            # Second call: return no hits
            return {"hits": {"total": {"value": 10}, "hits": []}}

        self.service.elasticsearch_service.client.get.side_effect = get_side_effect

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        flow_uuid = uuid.uuid4()

        results = self.service.get_flowsrun_results_by_contacts(
            report=report,
            flow_uuid=flow_uuid,
            start_date="2025-01-01",
            end_date="2025-01-02",
            op_field="user_feedback",
        )

        self.assertEqual(
            results,
            [
                {
                    "contact": {"name": "John Doe"},
                    "urn": "1234567890",
                    "modified_on": "2025-01-01",
                    "op_field_value": "5",
                }
            ],
        )

        cache_key = f"flowsrun_results_by_contacts:{report.uuid}:{flow_uuid}:2025-01-01:2025-01-02:user_feedback"

        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once_with(
            cache_key, json.dumps(results), ex=settings.REPORT_GENERATION_TIMEOUT
        )

    @patch("insights.sources.tests.mock.MockCacheClient.set")
    @patch("insights.sources.tests.mock.MockCacheClient.get")
    def test_get_flowsrun_results_by_contacts_when_no_results_exist(
        self, mock_cache_get, mock_cache_set
    ):
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None

        self.service.elasticsearch_service.client.get.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": [],
            }
        }

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        flow_uuid = uuid.uuid4()

        results = self.service.get_flowsrun_results_by_contacts(
            report=report,
            flow_uuid=flow_uuid,
            start_date="2025-01-01",
            end_date="2025-01-02",
            op_field="user_feedback",
        )

        self.assertEqual(results, [])

        cache_key = f"flowsrun_results_by_contacts:{report.uuid}:{flow_uuid}:2025-01-01:2025-01-02:user_feedback"

        mock_cache_get.assert_called_once_with(cache_key)
        mock_cache_set.assert_called_once_with(
            cache_key, json.dumps(results), ex=settings.REPORT_GENERATION_TIMEOUT
        )

    def test_get_flowsrun_results_by_contacts_when_report_is_failed(self):
        self.service.elasticsearch_service.client.get.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": [],
            }
        }

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            status=ReportStatus.FAILED,
            errors={"send_email": "test", "event_id": "test"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_flowsrun_results_by_contacts(
                report=report,
                flow_uuid=uuid.uuid4(),
                start_date="2025-01-01",
                end_date="2025-01-02",
                op_field="user_feedback",
            )

        self.assertEqual(
            str(context.exception),
            "Report %s is not in progress" % report.uuid,
        )

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_csat_ai_worksheet(self, mock_get_datalake_events):
        mock_events = [
            {
                "contact_urn": "123",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "5",
            }
        ]

        mock_get_datalake_events.return_value = mock_events

        agent_uuid = str(uuid.uuid4())

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["CSAT_AI"], "csat_ai_agent_uuid": agent_uuid},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        worksheet = self.service.get_csat_ai_worksheet(
            report, "2025-01-01", "2025-01-02"
        )

        self.assertEqual(worksheet.name, "CSAT AI")
        self.assertEqual(
            worksheet.data,
            [
                {
                    "URN": "123",
                    "Date": "14/09/2025 19:27:10",
                    "Rating": "5",
                }
            ],
        )

    def test_get_csat_ai_worksheet_when_no_agent_uuid_is_provided(self):
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["CSAT_AI"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_csat_ai_worksheet(report, "2025-01-01", "2025-01-02")

        self.assertEqual(
            str(context.exception),
            "Agent UUID is required in the report source config",
        )

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_custom_widget_worksheet(self, mock_get_datalake_events):
        mock_get_datalake_events.return_value = [
            {
                "contact_urn": "1234567890",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "5",
            }
        ]

        widget = Widget.objects.create(
            name="Test",
            config={"datalake_config": {"key": "test", "agent_uuid": "test"}},
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"custom_widgets": [str(widget.uuid)]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )
        worksheet = self.service.get_custom_widget_worksheet(
            report=report,
            widget=widget,
            start_date=datetime.fromisoformat("2025-01-01"),
            end_date=datetime.fromisoformat("2025-01-02"),
        )

        self.assertEqual(worksheet.name, widget.name)
        self.assertEqual(
            worksheet.data,
            [
                {
                    "URN": "1234567890",
                    "Date": "14/09/2025 19:27:10",
                    "Value": "5",
                }
            ],
        )


class TestSerializeFiltersForJson(TestCase):
    """Test cases for the serialize_filters_for_json utility function."""

    def test_serialize_empty_filters(self):
        """Test serialization of empty filters."""
        result = serialize_filters_for_json({})
        self.assertEqual(result, {})

    def test_serialize_none_filters(self):
        """Test serialization of None filters."""
        result = serialize_filters_for_json(None)
        self.assertEqual(result, None)

    def test_serialize_datetime_filters(self):
        """Test serialization of filters containing datetime objects."""
        now = timezone.now()
        filters = {
            "start": now,
            "end": now + timedelta(days=1),
            "string_field": "test",
            "number_field": 123,
        }

        result = serialize_filters_for_json(filters)

        self.assertEqual(result["start"], now.isoformat())
        self.assertEqual(result["end"], (now + timedelta(days=1)).isoformat())
        self.assertEqual(result["string_field"], "test")
        self.assertEqual(result["number_field"], 123)

    def test_serialize_nested_dict_filters(self):
        """Test serialization of filters with nested dictionaries containing datetime objects."""
        now = timezone.now()
        filters = {
            "date_range": {
                "start": now,
                "end": now + timedelta(days=1),
            },
            "other_field": "test",
        }

        result = serialize_filters_for_json(filters)

        self.assertEqual(result["date_range"]["start"], now.isoformat())
        self.assertEqual(
            result["date_range"]["end"], (now + timedelta(days=1)).isoformat()
        )
        self.assertEqual(result["other_field"], "test")

    def test_serialize_list_filters(self):
        """Test serialization of filters with lists containing datetime objects."""
        now = timezone.now()
        filters = {
            "dates": [now, now + timedelta(days=1)],
            "mixed_list": [now, "string", 123],
        }

        result = serialize_filters_for_json(filters)

        self.assertEqual(
            result["dates"], [now.isoformat(), (now + timedelta(days=1)).isoformat()]
        )
        self.assertEqual(result["mixed_list"], [now.isoformat(), "string", 123])

    def test_serialize_complex_nested_filters(self):
        """Test serialization of complex nested filters with datetime objects."""
        now = timezone.now()
        filters = {
            "level1": {
                "level2": {
                    "datetime_field": now,
                    "list_with_datetime": [now, now + timedelta(hours=1)],
                },
                "simple_field": "test",
            },
            "top_level_datetime": now + timedelta(days=1),
        }

        result = serialize_filters_for_json(filters)

        self.assertEqual(result["level1"]["level2"]["datetime_field"], now.isoformat())
        self.assertEqual(
            result["level1"]["level2"]["list_with_datetime"],
            [now.isoformat(), (now + timedelta(hours=1)).isoformat()],
        )
        self.assertEqual(result["level1"]["simple_field"], "test")
        self.assertEqual(
            result["top_level_datetime"], (now + timedelta(days=1)).isoformat()
        )
