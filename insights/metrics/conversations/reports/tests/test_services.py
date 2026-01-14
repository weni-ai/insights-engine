from datetime import datetime
import json
from unittest.mock import MagicMock, patch
import uuid

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)
from insights.metrics.conversations.reports.dataclass import (
    ConversationsReportWorksheet,
    ConversationsReportFile,
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
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
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
        mock_get_resolutions_worksheet,
        mock_send_email,
    ):
        mock_send_email.return_value = None
        mock_get_resolutions_worksheet.return_value = ConversationsReportWorksheet(
            name="Resolutions",
            data=[{"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}],
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

    def test_serialize_filters_with_none_values(self):
        """Test serialization of filters with None values."""
        filters = {
            "start": None,
            "end": None,
            "string_field": "test",
        }

        result = serialize_filters_for_json(filters)

        self.assertEqual(result["start"], None)
        self.assertEqual(result["end"], None)
        self.assertEqual(result["string_field"], "test")


class TestConversationsReportServiceAdditional(TestCase):
    """Additional test cases for ConversationsReportService to increase coverage."""

    def setUp(self):
        self.service = ConversationsReportService(
            elasticsearch_service=ConversationsElasticsearchService(
                client=MockElasticsearchClient(),
            ),
            events_limit_per_page=5,
            page_limit=5,
            datalake_events_client=ClassificationMockDataLakeEventsClient(),
            metrics_service=ConversationsMetricsService(
                datalake_service=MagicMock(spec=BaseConversationsMetricsService),
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

    def test_generate_with_missing_start_date(self):
        """Test generate method with missing start date."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"end": "2025-01-02"},  # Missing start date
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
        ) as mock_send_email:
            mock_send_email.return_value = None

            self.service.generate(report)

            # Check that error email was sent
            mock_send_email.assert_called_once()
            call_args = mock_send_email.call_args
            self.assertEqual(
                call_args[0][0], report
            )  # First argument should be the report
            self.assertEqual(
                call_args[0][1], []
            )  # Second argument should be empty files list
            self.assertTrue(call_args[1]["is_error"])  # is_error should be True

    def test_generate_with_missing_end_date(self):
        """Test generate method with missing end date."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01"},  # Missing end date
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
        ) as mock_send_email:
            mock_send_email.return_value = None

            self.service.generate(report)

            # Check that error email was sent
            mock_send_email.assert_called_once()
            call_args = mock_send_email.call_args
            self.assertEqual(
                call_args[0][0], report
            )  # First argument should be the report
            self.assertEqual(
                call_args[0][1], []
            )  # Second argument should be empty files list
            self.assertTrue(call_args[1]["is_error"])  # is_error should be True

    def test_generate_with_interrupted_report(self):
        """Test generate method with interrupted report."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
            config={"interrupted": True},
        )

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_resolutions_worksheet"
        ) as mock_get_resolutions:
            mock_get_resolutions.return_value = ConversationsReportWorksheet(
                name="Resolutions",
                data=[{"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}],
            )

            # Should not raise exception and should return early
            self.service.generate(report)

    def test_generate_with_exception_during_processing(self):
        """Test generate method when exception occurs during processing."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_resolutions_worksheet"
        ) as mock_get_resolutions:
            mock_get_resolutions.side_effect = Exception("Test error")

            with patch(
                "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
            ) as mock_send_email:
                mock_send_email.return_value = None

                self.service.generate(report)

                # Check that error email was sent
                mock_send_email.assert_called_once()
                call_args = mock_send_email.call_args
                self.assertEqual(
                    call_args[0][0], report
                )  # First argument should be the report
                self.assertEqual(
                    call_args[0][1], []
                )  # Second argument should be empty files list
                self.assertTrue(call_args[1]["is_error"])  # is_error should be True

            report.refresh_from_db()
            self.assertEqual(report.status, ReportStatus.FAILED)
            self.assertIn("generate", report.errors)

    def test_generate_with_email_send_failure(self):
        """Test generate method when email sending fails."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.PENDING,
        )

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_resolutions_worksheet"
        ) as mock_get_resolutions:
            mock_get_resolutions.return_value = ConversationsReportWorksheet(
                name="Resolutions",
                data=[{"URN": "123", "Resolution": "Resolved", "Date": "2025-01-01"}],
            )

            with patch(
                "insights.metrics.conversations.reports.services.ConversationsReportService.send_email"
            ) as mock_send_email:
                mock_send_email.side_effect = Exception("Email send failed")

                with self.assertRaises(Exception):
                    self.service.generate(report)

                report.refresh_from_db()
                self.assertEqual(report.status, ReportStatus.FAILED)
                self.assertIn("send_email", report.errors)

    def test_get_datalake_events_with_cached_data(self):
        """Test get_datalake_events with cached data."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        cached_events = [{"id": "1"}, {"id": "2"}]
        cache_key = f"datalake_events:{report.uuid}:{json.dumps({}, sort_keys=True, default=str)}"

        # Mock the cache client directly on the service instance
        with patch.object(self.service.cache_client, "get") as mock_cache_get:
            with patch.object(self.service.cache_client, "set") as mock_cache_set:
                mock_cache_get.return_value = json.dumps(cached_events)
                mock_cache_set.return_value = None

                # Mock the datalake events client to avoid hitting page limit
                with patch.object(
                    self.service.datalake_events_client, "get_events"
                ) as mock_get_events:
                    mock_get_events.return_value = []

                    events = self.service.get_datalake_events(report)

                    self.assertEqual(events, cached_events)
                    mock_cache_get.assert_called_once_with(cache_key)

    def test_get_datalake_events_with_invalid_cached_data(self):
        """Test get_datalake_events with invalid cached data."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        with patch("insights.sources.tests.mock.MockCacheClient.get") as mock_cache_get:
            mock_cache_get.return_value = "invalid json"

            with patch(
                "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
            ) as mock_get_events:
                mock_get_events.return_value = []

                events = self.service.get_datalake_events(report)

                self.assertEqual(events, [])

    def test_get_datalake_events_with_empty_events(self):
        """Test get_datalake_events with empty events list."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        with patch(
            "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
        ) as mock_get_events:
            mock_get_events.return_value = [{}]  # Empty dict

            events = self.service.get_datalake_events(report)

            self.assertEqual(events, [])

    def test_format_date_with_various_formats(self):
        """Test _format_date with various date formats."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        # Test with timezone
        self.project.timezone = "America/New_York"
        self.project.save()

        # Test ISO format
        result = self.service._format_date("2025-01-01T12:00:00", report)
        self.assertIn("01/01/2025", result)

        # Test with microseconds
        result = self.service._format_date("2025-01-01T12:00:00.000000Z", report)
        self.assertIn("01/01/2025", result)

        # Test with timestamp in milliseconds
        result = self.service._format_date(1759965431207, report)
        self.assertIn("08/10/2025", result)

        result = self.service._format_date(1759965431, report)
        self.assertIn("08/10/2025", result)

    def test_format_date_with_invalid_format(self):
        """Test _format_date with invalid date format."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        result = self.service._format_date("invalid-date", report)

        # Fallback to original date
        self.assertEqual(result, "invalid-date")

    def test_get_resolutions_worksheet_with_no_events(self):
        """Test get_resolutions_worksheet with no events."""
        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = []

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={},
                filters={},
                format=ReportFormat.CSV,
                requested_by=self.user,
            )

            worksheet = self.service.get_resolutions_worksheet(
                report, "2025-01-01", "2025-01-02"
            )

            self.assertEqual(worksheet.name, "Resolutions")
            self.assertEqual(len(worksheet.data), 0)  # No data when no events

    def test_get_resolutions_worksheet_with_events(self):
        """Test get_resolutions_worksheet with events."""
        mock_events = [
            {
                "contact_urn": "123",
                "date": "2025-01-01T12:00:00.000000Z",
                "value": "resolved",
            },
            {
                "contact_urn": "456",
                "date": "2025-01-01T12:00:00.000000Z",
                "value": "unresolved",
            },
            {
                "contact_urn": "789",
                "date": "2025-01-01T12:00:00.000000Z",
                "value": "Has Chats",
                "metadata": json.dumps(
                    {
                        "human_support": True,
                    }
                ),
            },
        ]

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = mock_events

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={},
                filters={},
                format=ReportFormat.CSV,
                requested_by=self.user,
            )

            worksheet = self.service.get_resolutions_worksheet(
                report, "2025-01-01", "2025-01-02"
            )

            self.assertEqual(worksheet.name, "Resolutions")
            self.assertEqual(len(worksheet.data), 3)
            self.assertEqual(worksheet.data[0]["URN"], "123")
            self.assertEqual(worksheet.data[0]["Resolution"], "AI-Assisted")
            self.assertEqual(worksheet.data[1]["URN"], "456")
            self.assertEqual(worksheet.data[1]["Resolution"], "Not assisted")
            self.assertEqual(worksheet.data[2]["URN"], "789")
            self.assertEqual(
                worksheet.data[2]["Resolution"], "Transferred to human support"
            )

    def test_get_topics_distribution_worksheet_for_human(self):
        """Test get_topics_distribution_worksheet for human conversations."""
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

        with patch(
            "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
        ) as mock_get_topics:
            mock_get_topics.return_value = [nexus_topics_data]

            with patch(
                "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
            ) as mock_get_events:
                mock_get_events.return_value = [
                    {
                        "contact_urn": "1",
                        "date": "2025-01-01T00:00:00.000000Z",
                        "metadata": json.dumps(
                            {
                                "topic_uuid": str(nexus_topics_data["uuid"]),
                                "subtopic_uuid": str(
                                    nexus_topics_data["subtopic"][0]["uuid"]
                                ),
                                "subtopic": nexus_topics_data["subtopic"][0]["name"],
                            }
                        ),
                        "value": nexus_topics_data["name"],
                    }
                ]

                report = Report.objects.create(
                    project=self.project,
                    source=self.service.source,
                    source_config={"sections": ["TOPICS_HUMAN"]},
                    filters={"start": "2025-01-01", "end": "2025-01-02"},
                    requested_by=self.user,
                )

                worksheet = self.service.get_topics_distribution_worksheet(
                    report,
                    datetime(2025, 1, 1),
                    datetime(2025, 1, 2),
                    ConversationType.HUMAN,
                )

                self.assertIsInstance(worksheet, ConversationsReportWorksheet)
                self.assertEqual(worksheet.name, "Topics Distribution Human")

    def test_get_topics_distribution_worksheet_with_invalid_metadata(self):
        """Test get_topics_distribution_worksheet with invalid metadata."""
        with patch(
            "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
        ) as mock_get_topics:
            mock_get_topics.return_value = []

            with patch(
                "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
            ) as mock_get_events:
                mock_get_events.return_value = [
                    {
                        "contact_urn": "1",
                        "date": "2025-01-01T00:00:00.000000Z",
                        "metadata": "invalid json",
                        "value": "Test Topic",
                    }
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
                self.assertEqual(len(worksheet.data), 1)  # Empty row when no events

    def test_get_topics_distribution_worksheet_with_no_events(self):
        """Test get_topics_distribution_worksheet with no events."""
        with patch(
            "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
        ) as mock_get_topics:
            mock_get_topics.return_value = []

            with patch(
                "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
            ) as mock_get_events:
                mock_get_events.return_value = []

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
                self.assertEqual(len(worksheet.data), 1)  # Empty row

    def test_get_csat_ai_worksheet_with_invalid_ratings(self):
        """Test get_csat_ai_worksheet with invalid ratings."""
        mock_events = [
            {
                "contact_urn": "123",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "5",  # Valid rating
            },
            {
                "contact_urn": "456",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "6",  # Invalid rating
            },
            {
                "contact_urn": "789",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "invalid",  # Invalid rating
            },
        ]

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = mock_events

            agent_uuid = str(uuid.uuid4())

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={
                    "sections": ["CSAT_AI"],
                    "csat_ai_agent_uuid": agent_uuid,
                },
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                format=ReportFormat.CSV,
                requested_by=self.user,
                status=ReportStatus.IN_PROGRESS,
            )

            worksheet = self.service.get_csat_ai_worksheet(
                report, datetime(2025, 1, 1), datetime(2025, 1, 2)
            )

            self.assertEqual(worksheet.name, "CSAT AI")
            self.assertEqual(len(worksheet.data), 1)  # Only valid rating included

    def test_get_csat_ai_worksheet_with_no_events(self):
        """Test get_csat_ai_worksheet with no events."""
        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = []

            agent_uuid = str(uuid.uuid4())

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={
                    "sections": ["CSAT_AI"],
                    "csat_ai_agent_uuid": agent_uuid,
                },
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                format=ReportFormat.CSV,
                requested_by=self.user,
                status=ReportStatus.IN_PROGRESS,
            )

            worksheet = self.service.get_csat_ai_worksheet(
                report, datetime(2025, 1, 1), datetime(2025, 1, 2)
            )

            self.assertEqual(worksheet.name, "CSAT AI")
            self.assertEqual(len(worksheet.data), 1)  # Empty row

    def test_get_nps_ai_worksheet_with_invalid_ratings(self):
        """Test get_nps_ai_worksheet with invalid ratings."""
        mock_events = [
            {
                "contact_urn": "123",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "5",  # Valid rating
            },
            {
                "contact_urn": "456",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "11",  # Invalid rating
            },
            {
                "contact_urn": "789",
                "date": "2025-09-14T19:27:10.293700Z",
                "value": "invalid",  # Invalid rating
            },
        ]

        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = mock_events

            agent_uuid = str(uuid.uuid4())

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={"sections": ["NPS_AI"], "nps_ai_agent_uuid": agent_uuid},
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                format=ReportFormat.CSV,
                requested_by=self.user,
                status=ReportStatus.IN_PROGRESS,
            )

            worksheet = self.service.get_nps_ai_worksheet(
                report, datetime(2025, 1, 1), datetime(2025, 1, 2)
            )

            self.assertEqual(worksheet.name, "NPS AI")
            self.assertEqual(len(worksheet.data), 1)  # Only valid rating included

    def test_get_nps_ai_worksheet_with_no_agent_uuid(self):
        """Test get_nps_ai_worksheet when no agent UUID is provided."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["NPS_AI"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_nps_ai_worksheet(
                report, datetime(2025, 1, 1), datetime(2025, 1, 2)
            )

        self.assertEqual(
            str(context.exception),
            "Agent UUID is required in the report source config",
        )

    def test_get_csat_human_worksheet_with_missing_flow_uuid(self):
        """Test get_csat_human_worksheet with missing flow UUID."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["CSAT_HUMAN"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_csat_human_worksheet(report, "2025-01-01", "2025-01-02")

        self.assertIn("flow_uuid", str(context.exception))

    def test_get_csat_human_worksheet_with_missing_op_field(self):
        """Test get_csat_human_worksheet with missing op field."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={
                "sections": ["CSAT_HUMAN"],
                "csat_human_flow_uuid": str(uuid.uuid4()),
            },
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_csat_human_worksheet(report, "2025-01-01", "2025-01-02")

        self.assertIn("op_field", str(context.exception))

    def test_get_csat_human_worksheet_with_none_values(self):
        """Test get_csat_human_worksheet with None values in results."""
        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_flowsrun_results_by_contacts"
        ) as mock_get_results:
            mock_get_results.return_value = [
                {
                    "urn": "123",
                    "modified_on": "2025-01-01T12:00:00.000000Z",
                    "op_field_value": "5",
                },
                {
                    "urn": "456",
                    "modified_on": "2025-01-01T12:00:00.000000Z",
                    "op_field_value": None,  # Should be filtered out
                },
            ]

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={
                    "sections": ["CSAT_HUMAN"],
                    "csat_human_flow_uuid": str(uuid.uuid4()),
                    "csat_human_op_field": "test_field",
                },
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                format=ReportFormat.CSV,
                requested_by=self.user,
                status=ReportStatus.IN_PROGRESS,
            )

            worksheet = self.service.get_csat_human_worksheet(
                report, "2025-01-01", "2025-01-02"
            )

            self.assertEqual(worksheet.name, "CSAT Human")
            self.assertEqual(len(worksheet.data), 1)  # Only non-None value included

    def test_get_nps_human_worksheet_with_missing_flow_uuid(self):
        """Test get_nps_human_worksheet with missing flow UUID."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["NPS_HUMAN"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_nps_human_worksheet(report, "2025-01-01", "2025-01-02")

        self.assertIn("flow_uuid", str(context.exception))

    def test_get_nps_human_worksheet_with_missing_op_field(self):
        """Test get_nps_human_worksheet with missing op field."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={
                "sections": ["NPS_HUMAN"],
                "nps_human_flow_uuid": str(uuid.uuid4()),
            },
            filters={"start": "2025-01-01", "end": "2025-01-02"},
        )

        with self.assertRaises(ValueError) as context:
            self.service.get_nps_human_worksheet(report, "2025-01-01", "2025-01-02")

        self.assertIn("op_field", str(context.exception))

    def test_get_nps_human_worksheet_with_none_values(self):
        """Test get_nps_human_worksheet with None values in results."""
        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_flowsrun_results_by_contacts"
        ) as mock_get_results:
            mock_get_results.return_value = [
                {
                    "urn": "123",
                    "modified_on": "2025-01-01T12:00:00.000000Z",
                    "op_field_value": "5",
                },
                {
                    "urn": "456",
                    "modified_on": "2025-01-01T12:00:00.000000Z",
                    "op_field_value": None,  # Should be filtered out
                },
            ]

            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={
                    "sections": ["NPS_HUMAN"],
                    "nps_human_flow_uuid": str(uuid.uuid4()),
                    "nps_human_op_field": "test_field",
                },
                filters={"start": "2025-01-01", "end": "2025-01-02"},
                format=ReportFormat.CSV,
                requested_by=self.user,
                status=ReportStatus.IN_PROGRESS,
            )

            worksheet = self.service.get_nps_human_worksheet(
                report, "2025-01-01", "2025-01-02"
            )

            self.assertEqual(worksheet.name, "NPS Human")
            self.assertEqual(len(worksheet.data), 1)  # Only non-None value included

    def test_get_custom_widget_worksheet_with_missing_key(self):
        """Test get_custom_widget_worksheet with missing key in config."""
        widget = Widget.objects.create(
            name="Test",
            config={"datalake_config": {"agent_uuid": "test"}},  # Missing key
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

        with self.assertRaises(ValueError) as context:
            self.service.get_custom_widget_worksheet(
                report=report,
                widget=widget,
                start_date=datetime.fromisoformat("2025-01-01"),
                end_date=datetime.fromisoformat("2025-01-02"),
            )

        self.assertIn("Key or agent_uuid is missing", str(context.exception))

    def test_get_custom_widget_worksheet_with_missing_agent_uuid(self):
        """Test get_custom_widget_worksheet with missing agent_uuid in config."""
        widget = Widget.objects.create(
            name="Test",
            config={"datalake_config": {"key": "test"}},  # Missing agent_uuid
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

        with self.assertRaises(ValueError) as context:
            self.service.get_custom_widget_worksheet(
                report=report,
                widget=widget,
                start_date=datetime.fromisoformat("2025-01-01"),
                end_date=datetime.fromisoformat("2025-01-02"),
            )

        self.assertIn("Key or agent_uuid is missing", str(context.exception))

    def test_get_custom_widget_worksheet_with_no_events(self):
        """Test get_custom_widget_worksheet with no events."""
        with patch(
            "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
        ) as mock_get_events:
            mock_get_events.return_value = []

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
            self.assertEqual(len(worksheet.data), 1)  # Empty row

    def test_get_flowsrun_results_by_contacts_with_cached_data(self):
        """Test get_flowsrun_results_by_contacts with cached data."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        cached_results = [{"urn": "123", "op_field_value": "5"}]
        flow_uuid = uuid.uuid4()
        cache_key = f"flowsrun_results_by_contacts:{report.uuid}:{flow_uuid}:2025-01-01:2025-01-02:user_feedback"

        # Mock the cache client directly on the service instance
        with patch.object(self.service.cache_client, "get") as mock_cache_get:
            with patch.object(self.service.cache_client, "set") as mock_cache_set:
                mock_cache_get.return_value = json.dumps(cached_results)
                mock_cache_set.return_value = None

                # Mock the elasticsearch service to avoid hitting page limit
                with patch.object(
                    self.service.elasticsearch_service,
                    "get_flowsrun_results_by_contacts",
                ) as mock_get_results:
                    mock_get_results.return_value = {
                        "contacts": []
                    }  # Empty response to avoid page limit

                    results = self.service.get_flowsrun_results_by_contacts(
                        report=report,
                        flow_uuid=flow_uuid,
                        start_date="2025-01-01",
                        end_date="2025-01-02",
                        op_field="user_feedback",
                    )

                    self.assertEqual(results, cached_results)
                    mock_cache_get.assert_called_once_with(cache_key)

    def test_get_flowsrun_results_by_contacts_with_invalid_cached_data(self):
        """Test get_flowsrun_results_by_contacts with invalid cached data."""
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

        with patch("insights.sources.tests.mock.MockCacheClient.get") as mock_cache_get:
            mock_cache_get.return_value = "invalid json"

            with patch(
                "insights.metrics.conversations.integrations.elasticsearch.services.ConversationsElasticsearchService.get_flowsrun_results_by_contacts"
            ) as mock_get_results:
                mock_get_results.return_value = {"contacts": []}

                results = self.service.get_flowsrun_results_by_contacts(
                    report=report,
                    flow_uuid=flow_uuid,
                    start_date="2025-01-01",
                    end_date="2025-01-02",
                    op_field="user_feedback",
                )

                self.assertEqual(results, [])

    def test_get_flowsrun_results_by_contacts_with_page_limit_reached(self):
        """Test get_flowsrun_results_by_contacts when page limit is reached."""
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

        def get_side_effect(*args, **kwargs):
            # Always return contacts to trigger page limit
            return {
                "hits": {
                    "total": {"value": 10},
                    "hits": [{"_source": {"contact_urn": "123"}}],
                }
            }

        self.service.elasticsearch_service.client.get.side_effect = get_side_effect

        with self.assertRaises(ValueError) as context:
            self.service.get_flowsrun_results_by_contacts(
                report=report,
                flow_uuid=flow_uuid,
                start_date="2025-01-01",
                end_date="2025-01-02",
                op_field="user_feedback",
            )

        self.assertIn("Report has more than", str(context.exception))

    def test_get_flowsrun_results_by_contacts_with_empty_contacts(self):
        """Test get_flowsrun_results_by_contacts with empty contacts."""
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

        self.service.elasticsearch_service.client.get.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": [],
            }
        }

        results = self.service.get_flowsrun_results_by_contacts(
            report=report,
            flow_uuid=flow_uuid,
            start_date="2025-01-01",
            end_date="2025-01-02",
            op_field="user_feedback",
        )

        self.assertEqual(results, [])

    @patch("insights.metrics.conversations.reports.services.get_custom_widgets")
    @patch("insights.metrics.conversations.reports.services.get_nps_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_nps_ai_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_ai_widget")
    def test_get_available_widgets_basic_only(
        self,
        mock_get_csat_ai_widget,
        mock_get_nps_ai_widget,
        mock_get_csat_human_widget,
        mock_get_nps_human_widget,
        mock_get_custom_widgets,
    ):
        """Test get_available_widgets with only basic widgets (no special widgets)."""
        # Mock all special widget functions to return None
        mock_get_csat_ai_widget.return_value = None
        mock_get_nps_ai_widget.return_value = None
        mock_get_csat_human_widget.return_value = None
        mock_get_nps_human_widget.return_value = None
        mock_get_custom_widgets.return_value = []

        result = self.service.get_available_widgets(self.project)

        # Should only contain basic widgets
        expected_sections = ["RESOLUTIONS", "TRANSFERRED", "TOPICS_AI", "TOPICS_HUMAN"]
        self.assertEqual(result.sections, expected_sections)
        self.assertEqual(result.custom_widgets, [])

        # Verify all special widget functions were called
        mock_get_csat_ai_widget.assert_called_once_with(self.project)
        mock_get_nps_ai_widget.assert_called_once_with(self.project)
        mock_get_csat_human_widget.assert_called_once_with(self.project)
        mock_get_nps_human_widget.assert_called_once_with(self.project)
        mock_get_custom_widgets.assert_called_once_with(self.project)

    @patch("insights.metrics.conversations.reports.services.get_custom_widgets")
    @patch("insights.metrics.conversations.reports.services.get_nps_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_nps_ai_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_ai_widget")
    def test_get_available_widgets_with_special_widgets(
        self,
        mock_get_csat_ai_widget,
        mock_get_nps_ai_widget,
        mock_get_csat_human_widget,
        mock_get_nps_human_widget,
        mock_get_custom_widgets,
    ):
        """Test get_available_widgets with special widgets available."""
        # Mock special widget functions to return mock widgets
        mock_csat_ai_widget = Widget.objects.create(
            name="CSAT AI Widget",
            config={"datalake_config": {"agent_uuid": "test-uuid"}},
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )
        mock_nps_ai_widget = Widget.objects.create(
            name="NPS AI Widget",
            config={"datalake_config": {"agent_uuid": "test-uuid"}},
            source="conversations.nps",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )
        mock_csat_human_widget = Widget.objects.create(
            name="CSAT Human Widget",
            config={
                "type": "flow_result",
                "filter": {"flow": "test-flow"},
                "op_field": "test_field",
            },
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )
        mock_nps_human_widget = Widget.objects.create(
            name="NPS Human Widget",
            config={
                "type": "flow_result",
                "filter": {"flow": "test-flow"},
                "op_field": "test_field",
            },
            source="conversations.nps",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_csat_ai_widget.return_value = mock_csat_ai_widget
        mock_get_nps_ai_widget.return_value = mock_nps_ai_widget
        mock_get_csat_human_widget.return_value = mock_csat_human_widget
        mock_get_nps_human_widget.return_value = mock_nps_human_widget
        mock_get_custom_widgets.return_value = []

        result = self.service.get_available_widgets(self.project)

        # Should contain basic widgets plus special widgets
        expected_sections = [
            "RESOLUTIONS",
            "TRANSFERRED",
            "TOPICS_AI",
            "TOPICS_HUMAN",
            "CSAT_AI",
            "CSAT_HUMAN",
            "NPS_AI",
            "NPS_HUMAN",
        ]
        self.assertEqual(result.sections, expected_sections)
        self.assertEqual(result.custom_widgets, [])

    @patch("insights.metrics.conversations.reports.services.get_custom_widgets")
    @patch("insights.metrics.conversations.reports.services.get_nps_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_nps_ai_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_ai_widget")
    def test_get_available_widgets_with_custom_widgets(
        self,
        mock_get_csat_ai_widget,
        mock_get_nps_ai_widget,
        mock_get_csat_human_widget,
        mock_get_nps_human_widget,
        mock_get_custom_widgets,
    ):
        """Test get_available_widgets with custom widgets available."""
        # Mock special widget functions to return None
        mock_get_csat_ai_widget.return_value = None
        mock_get_nps_ai_widget.return_value = None
        mock_get_csat_human_widget.return_value = None
        mock_get_nps_human_widget.return_value = None

        # Create custom widgets
        custom_widget1 = Widget.objects.create(
            name="Custom Widget 1",
            config={"datalake_config": {"key": "test1", "agent_uuid": "test-uuid"}},
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )
        custom_widget2 = Widget.objects.create(
            name="Custom Widget 2",
            config={"datalake_config": {"key": "test2", "agent_uuid": "test-uuid"}},
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_custom_widgets.return_value = [
            custom_widget1.uuid,
            custom_widget2.uuid,
        ]

        result = self.service.get_available_widgets(self.project)

        # Should contain basic widgets and custom widgets
        expected_sections = ["RESOLUTIONS", "TRANSFERRED", "TOPICS_AI", "TOPICS_HUMAN"]
        self.assertEqual(result.sections, expected_sections)
        self.assertEqual(
            result.custom_widgets, [custom_widget1.uuid, custom_widget2.uuid]
        )

    @patch("insights.metrics.conversations.reports.services.get_custom_widgets")
    @patch("insights.metrics.conversations.reports.services.get_nps_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_nps_ai_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_ai_widget")
    def test_get_available_widgets_combined(
        self,
        mock_get_csat_ai_widget,
        mock_get_nps_ai_widget,
        mock_get_csat_human_widget,
        mock_get_nps_human_widget,
        mock_get_custom_widgets,
    ):
        """Test get_available_widgets with all types of widgets available."""
        # Mock special widget functions to return mock widgets
        mock_csat_ai_widget = Widget.objects.create(
            name="CSAT AI Widget",
            config={"datalake_config": {"agent_uuid": "test-uuid"}},
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )
        mock_nps_ai_widget = Widget.objects.create(
            name="NPS AI Widget",
            config={"datalake_config": {"agent_uuid": "test-uuid"}},
            source="conversations.nps",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_csat_ai_widget.return_value = mock_csat_ai_widget
        mock_get_nps_ai_widget.return_value = mock_nps_ai_widget
        mock_get_csat_human_widget.return_value = None
        mock_get_nps_human_widget.return_value = None

        # Create custom widgets
        custom_widget = Widget.objects.create(
            name="Custom Widget",
            config={"datalake_config": {"key": "test", "agent_uuid": "test-uuid"}},
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_custom_widgets.return_value = [custom_widget.uuid]

        result = self.service.get_available_widgets(self.project)

        # Should contain basic widgets, some special widgets, and custom widgets
        expected_sections = [
            "RESOLUTIONS",
            "TRANSFERRED",
            "TOPICS_AI",
            "TOPICS_HUMAN",
            "CSAT_AI",
            "NPS_AI",
        ]
        self.assertEqual(result.sections, expected_sections)
        self.assertEqual(result.custom_widgets, [custom_widget.uuid])

    @patch("insights.metrics.conversations.reports.services.get_custom_widgets")
    @patch("insights.metrics.conversations.reports.services.get_nps_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_human_widget")
    @patch("insights.metrics.conversations.reports.services.get_nps_ai_widget")
    @patch("insights.metrics.conversations.reports.services.get_csat_ai_widget")
    def test_get_available_widgets_partial_special_widgets(
        self,
        mock_get_csat_ai_widget,
        mock_get_nps_ai_widget,
        mock_get_csat_human_widget,
        mock_get_nps_human_widget,
        mock_get_custom_widgets,
    ):
        """Test get_available_widgets with only some special widgets available."""
        # Mock only some special widget functions to return widgets
        mock_csat_ai_widget = Widget.objects.create(
            name="CSAT AI Widget",
            config={"datalake_config": {"agent_uuid": "test-uuid"}},
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_csat_ai_widget.return_value = mock_csat_ai_widget
        mock_get_nps_ai_widget.return_value = None
        mock_get_csat_human_widget.return_value = None
        mock_get_nps_human_widget.return_value = None
        mock_get_custom_widgets.return_value = []

        result = self.service.get_available_widgets(self.project)

        # Should contain basic widgets plus only CSAT_AI
        expected_sections = [
            "RESOLUTIONS",
            "TRANSFERRED",
            "TOPICS_AI",
            "TOPICS_HUMAN",
            "CSAT_AI",
        ]
        self.assertEqual(result.sections, expected_sections)
        self.assertEqual(result.custom_widgets, [])

    def test_zip_files_with_single_file(self):
        """Test zip_files with a single file."""
        file = ConversationsReportFile(name="test.csv", content=b"test content")
        result = self.service.zip_files([file])

        self.assertEqual(result.name, "conversations_report.zip")
        self.assertIsInstance(result.content, bytes)
        self.assertGreater(len(result.content), 0)

    def test_zip_files_with_multiple_files(self):
        """Test zip_files with multiple files."""
        file1 = ConversationsReportFile(name="test1.csv", content=b"content1")
        file2 = ConversationsReportFile(name="test2.csv", content=b"content2")
        result = self.service.zip_files([file1, file2])

        self.assertEqual(result.name, "conversations_report.zip")
        self.assertIsInstance(result.content, bytes)
        self.assertGreater(len(result.content), 0)

    def test_zip_files_with_duplicate_names(self):
        """Test zip_files with duplicate file names."""
        file1 = ConversationsReportFile(name="test.csv", content=b"content1")
        file2 = ConversationsReportFile(name="test.csv", content=b"content2")
        result = self.service.zip_files([file1, file2])

        self.assertEqual(result.name, "conversations_report.zip")
        self.assertIsInstance(result.content, bytes)
        self.assertGreater(len(result.content), 0)

    @patch("boto3.client")
    def test_upload_file_to_s3(self, mock_boto3_client):
        """Test upload_file_to_s3 method."""
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        file = ConversationsReportFile(name="test.csv", content=b"test content")
        obj_key = self.service.upload_file_to_s3(file)

        self.assertIsNotNone(obj_key)
        self.assertIn("reports/conversations/", obj_key)
        self.assertIn(".csv", obj_key)
        mock_s3_client.upload_fileobj.assert_called_once()

    @patch("boto3.client")
    def test_get_presigned_url(self, mock_boto3_client):
        """Test get_presigned_url method."""
        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"
        mock_boto3_client.return_value = mock_s3_client

        obj_key = "reports/conversations/test.csv"
        url = self.service.get_presigned_url(obj_key)

        self.assertEqual(url, "https://presigned-url.com")
        mock_s3_client.generate_presigned_url.assert_called_once()

    @patch("django.core.mail.EmailMessage.send")
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_presigned_url"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.upload_file_to_s3"
    )
    def test_send_email_with_multiple_files_and_s3(
        self, mock_upload, mock_get_presigned, mock_send_email
    ):
        """Test send_email with multiple files and S3 enabled."""
        mock_upload.return_value = "reports/conversations/test.zip"
        mock_get_presigned.return_value = "https://presigned-url.com"
        mock_send_email.return_value = None

        with patch("django.conf.settings.USE_S3", True):
            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={},
                filters={},
                format=ReportFormat.CSV,
                requested_by=self.user,
            )

            files = [
                ConversationsReportFile(name="test1.csv", content=b"content1"),
                ConversationsReportFile(name="test2.csv", content=b"content2"),
            ]

            self.service.send_email(report, files)

            mock_upload.assert_called_once()
            mock_get_presigned.assert_called_once()
            mock_send_email.assert_called_once()

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email_with_single_file_no_s3(self, mock_send_email):
        """Test send_email with single file and S3 disabled."""
        mock_send_email.return_value = None

        with patch("django.conf.settings.USE_S3", False):
            report = Report.objects.create(
                project=self.project,
                source=self.service.source,
                source_config={},
                filters={},
                format=ReportFormat.CSV,
                requested_by=self.user,
            )

            files = [ConversationsReportFile(name="test.csv", content=b"content")]

            self.service.send_email(report, files)

            mock_send_email.assert_called_once()

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email_with_no_files(self, mock_send_email):
        """Test send_email with no files."""
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.send_email(report, [])

        mock_send_email.assert_called_once()

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email_exception_handling(self, mock_send_email):
        """Test send_email exception handling."""
        mock_send_email.side_effect = Exception("Email send failed")

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        result = self.service.send_email(
            report, [ConversationsReportFile(name="test.csv", content=b"content")]
        )

        self.assertIsNone(result)
        mock_send_email.assert_called_once()

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_custom_widget_worksheet"
    )
    def test_get_worksheets_with_custom_widgets(self, mock_get_custom_widget):
        """Test _get_worksheets with custom widgets."""
        widget = Widget.objects.create(
            name="Custom Widget",
            config={"datalake_config": {"key": "test", "agent_uuid": "test-uuid"}},
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            dashboard=self.dashboard,
        )

        mock_get_custom_widget.return_value = ConversationsReportWorksheet(
            name="Custom Widget",
            data=[{"URN": "123", "Value": "test"}],
        )

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"custom_widgets": [str(widget.uuid)]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        worksheets = self.service._get_worksheets(
            report, datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        self.assertEqual(len(worksheets), 1)
        mock_get_custom_widget.assert_called_once()

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    def test_get_datalake_events_with_datetime_objects(self, mock_get_events):
        """Test get_datalake_events with datetime objects in kwargs."""
        mock_get_events.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["RESOLUTIONS"]},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 2)

        events = self.service.get_datalake_events(
            report, date_start=start_date, date_end=end_date
        )

        self.assertEqual(events, [])
        # Verify that datetime objects were converted to ISO format
        call_kwargs = mock_get_events.call_args[1]
        self.assertIsInstance(call_kwargs["date_start"], str)
        self.assertIsInstance(call_kwargs["date_end"], str)

    def test_format_date_with_timestamp_in_seconds(self):
        """Test _format_date with timestamp in seconds."""
        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        # Test with timestamp in seconds (not milliseconds)
        timestamp = 1735689600  # 2025-01-01 00:00:00 UTC
        result = self.service._format_date(timestamp, report)

        self.assertIn("01/01/2025", result)

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_resolutions_worksheet_with_empty_data(self, mock_get_events):
        """Test get_resolutions_worksheet with empty data returns empty list."""
        mock_get_events.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        worksheet = self.service.get_resolutions_worksheet(
            report, datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        # Should return empty list when no events (early return)
        self.assertEqual(len(worksheet.data), 0)

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_transferred_to_human_worksheet_with_empty_data(self, mock_get_events):
        """Test get_transferred_to_human_worksheet with empty data returns empty list."""
        mock_get_events.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        worksheet = self.service.get_transferred_to_human_worksheet(
            report, datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        # Should return empty list when no events (early return)
        self.assertEqual(len(worksheet.data), 0)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_topics_data_with_subtopics(self, mock_get_events, mock_get_topics):
        """Test _get_topics_data with subtopics."""
        topic_uuid = uuid.uuid4()
        subtopic_uuid = uuid.uuid4()

        mock_get_topics.return_value = [
            {
                "name": "Test Topic",
                "uuid": topic_uuid,
                "subtopic": [
                    {
                        "name": "Test Subtopic",
                        "uuid": subtopic_uuid,
                    }
                ],
            }
        ]

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        topics_data = self.service._get_topics_data(report)

        self.assertIn(str(topic_uuid), topics_data)
        self.assertIn(str(subtopic_uuid), topics_data[str(topic_uuid)]["subtopics"])

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_nps_ai_worksheet_with_empty_data(self, mock_get_events):
        """Test get_nps_ai_worksheet with empty data triggers empty row creation."""
        mock_get_events.return_value = []

        agent_uuid = str(uuid.uuid4())

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={"sections": ["NPS_AI"], "nps_ai_agent_uuid": agent_uuid},
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        worksheet = self.service.get_nps_ai_worksheet(
            report, datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        # Should have empty row when no events
        self.assertEqual(len(worksheet.data), 1)
        self.assertEqual(worksheet.data[0]["URN"], "")

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_flowsrun_results_by_contacts"
    )
    def test_get_csat_human_worksheet_with_empty_data(self, mock_get_results):
        """Test get_csat_human_worksheet with empty data triggers empty row creation."""
        mock_get_results.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={
                "sections": ["CSAT_HUMAN"],
                "csat_human_flow_uuid": str(uuid.uuid4()),
                "csat_human_op_field": "test_field",
            },
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        worksheet = self.service.get_csat_human_worksheet(
            report, "2025-01-01", "2025-01-02"
        )

        # Should have empty row when no events
        self.assertEqual(len(worksheet.data), 1)
        self.assertEqual(worksheet.data[0]["URN"], "")

    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_flowsrun_results_by_contacts"
    )
    def test_get_nps_human_worksheet_with_empty_data(self, mock_get_results):
        """Test get_nps_human_worksheet with empty data triggers empty row creation."""
        mock_get_results.return_value = []

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={
                "sections": ["NPS_HUMAN"],
                "nps_human_flow_uuid": str(uuid.uuid4()),
                "nps_human_op_field": "test_field",
            },
            filters={"start": "2025-01-01", "end": "2025-01-02"},
            format=ReportFormat.CSV,
            requested_by=self.user,
            status=ReportStatus.IN_PROGRESS,
        )

        worksheet = self.service.get_nps_human_worksheet(
            report, "2025-01-01", "2025-01-02"
        )

        # Should have empty row when no events
        self.assertEqual(len(worksheet.data), 1)
        self.assertEqual(worksheet.data[0]["URN"], "")

    def test_zip_files_with_many_duplicate_names(self):
        """Test zip_files handles many files with duplicate names successfully."""
        # Create multiple files with the same name to test name resolution
        files = [
            ConversationsReportFile(name="test.csv", content=b"content")
            for _ in range(5)
        ]

        result = self.service.zip_files(files)

        self.assertEqual(result.name, "conversations_report.zip")
        self.assertIsInstance(result.content, bytes)
        self.assertGreater(len(result.content), 0)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_topics_distribution_worksheet_with_invalid_metadata_skips_event(
        self, mock_get_events, mock_get_topics
    ):
        """Test get_topics_distribution_worksheet skips events with invalid metadata."""
        mock_get_topics.return_value = []

        mock_get_events.return_value = [
            {
                "contact_urn": "1",
                "date": "2025-01-01T00:00:00.000000Z",
                "metadata": "invalid json",  # Invalid JSON that will cause exception
                "value": "Test Topic",
            },
            {
                "contact_urn": "2",
                "date": "2025-01-01T00:00:00.000000Z",
                "metadata": json.dumps({"topic_uuid": str(uuid.uuid4())}),
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

        # Should skip the event with invalid metadata, only process the valid one
        self.assertIsInstance(worksheet, ConversationsReportWorksheet)
        # Should have empty row since the valid event will be unclassified
        self.assertEqual(len(worksheet.data), 1)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_topics"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_datalake_events"
    )
    def test_get_topics_distribution_worksheet_with_topic_but_no_subtopic_uuid(
        self, mock_get_events, mock_get_topics
    ):
        """Test get_topics_distribution_worksheet with topic UUID but no subtopic UUID."""
        topic_uuid = uuid.uuid4()

        mock_get_topics.return_value = [
            {
                "name": "Test Topic",
                "uuid": topic_uuid,
                "subtopic": [
                    {
                        "name": "Test Subtopic",
                        "uuid": uuid.uuid4(),
                    }
                ],
            }
        ]

        mock_get_events.return_value = [
            {
                "contact_urn": "1",
                "date": "2025-01-01T00:00:00.000000Z",
                "metadata": json.dumps(
                    {
                        "topic_uuid": str(topic_uuid),
                        # No subtopic_uuid - should be marked as unclassified
                    }
                ),
                "value": "Test Topic",
            }
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
        self.assertEqual(len(worksheet.data), 1)
        # Subtopic should be unclassified
        self.assertEqual(worksheet.data[0]["Subtopic"], "Unclassified")
