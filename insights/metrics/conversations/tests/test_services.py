from datetime import datetime, timedelta
import uuid
import json
from uuid import UUID
from unittest.mock import Mock, MagicMock, patch

from django.test import TestCase
from django.core.cache import cache


from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    AgentInvocationAgent,
    AgentInvocationItem,
    AgentInvocationMetrics,
    AvailableWidgetsList,
    ConversationsTotalsMetrics,
    ConversationsTotalsMetric,
    CrosstabItemData,
    CrosstabSubItemData,
    NPSMetrics,
    NPSMetricsField,
    SalesFunnelMetrics,
    ToolResultAgent,
    ToolResultItem,
    ToolResultMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import (
    AbsoluteNumbersMetricsType,
    AvailableWidgets,
    AvailableWidgetsListType,
    ConversationType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.metrics.conversations.integrations.datalake.dataclass import (
    ToolResultMetric,
    AgentInvocationMetric,
    SalesFunnelData,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.services import (
    ConversationsMetricsService,
)
from insights.projects.models import Project
from insights.sources.flowruns.usecases.query_execute import (
    QueryExecutor as FlowRunsQueryExecutor,
)
from insights.sources.integrations.clients import (
    NexusConversationsAPIClient,
)
from insights.sources.cache import CacheClient
from insights.widgets.models import Widget


class MockResponse:
    def __init__(self, status_code: int, content: str):
        self.status_code = status_code
        self.content = content

    @property
    def text(self):
        return self.content

    def json(self):
        return json.loads(self.content)


class TestConversationsMetricsService(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        # Create mocks with proper specs for type safety
        self.mock_datalake_service = Mock(spec=BaseDatalakeConversationsMetricsService)
        self.mock_nexus_conversations_client = MagicMock(
            spec=NexusConversationsAPIClient
        )
        self.mock_cache_client = Mock(spec=CacheClient)
        self.mock_flowruns_query_executor = Mock(spec=FlowRunsQueryExecutor)

        # Configure default mock return values
        self.mock_datalake_service.get_csat_metrics.return_value = {
            "1": 10,
            "2": 20,
            "3": 30,
            "4": 40,
            "5": 50,
        }
        self.mock_datalake_service.get_nps_metrics.return_value = {
            str(i): 10 for i in range(0, 11)
        }
        self.mock_datalake_service.get_conversations_totals.return_value = (
            ConversationsTotalsMetrics(
                total_conversations=ConversationsTotalsMetric(
                    value=100, percentage=100
                ),
                resolved=ConversationsTotalsMetric(value=60, percentage=60),
                unresolved=ConversationsTotalsMetric(value=40, percentage=40),
                transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
            )
        )
        self.mock_datalake_service.get_sales_funnel_data.return_value = SalesFunnelData(
            leads_count=100,
            total_orders_count=100,
            total_orders_value=100,
            currency_code="BRL",
        )
        self.mock_datalake_service.get_generic_metrics_by_key.return_value = {
            str(i): 10 for i in range(0, 11)
        }
        self.mock_datalake_service.get_topics_distribution.return_value = {
            "OTHER": {
                "name": "OTHER",
                "uuid": None,
                "count": 100,
                "subtopics": {},
            },
            str(uuid.uuid4()): {
                "name": "Cancelamento",
                "uuid": "2026cedc-67f6-4a04-977a-55cc581defa9",
                "count": 100,
                "subtopics": {
                    str(uuid.uuid4()): {
                        "name": "Subtopic 1",
                        "uuid": str(uuid.uuid4()),
                        "count": 70,
                    },
                    "OTHER": {
                        "name": "OTHER",
                        "uuid": None,
                        "count": 30,
                    },
                },
            },
        }

        # Configure nexus client mocks
        topics_data = {
            "results": [
                {
                    "name": "Cancelamento",
                    "uuid": "2026cedc-67f6-4a04-977a-55cc581defa9",
                    "created_at": "2025-07-15T20:56:47.582521Z",
                    "description": "Quando cliente pede para cancelar um pedido",
                    "subtopic": [
                        {
                            "name": "Subtopic 1",
                            "uuid": "023d2374-04ef-45b5-8b5f-5c031fafd59e",
                            "created_at": "2025-07-15T20:56:47.582521Z",
                            "description": "Quando cliente pede para cancelar um pedido",
                        },
                    ],
                }
            ]
        }

        self.mock_nexus_conversations_client.get_topics.return_value = MockResponse(
            200, json.dumps(topics_data)
        )
        self.mock_nexus_conversations_client.get_subtopics.return_value = MockResponse(
            200, json.dumps(topics_data)
        )
        self.mock_nexus_conversations_client.create_topic.return_value = MockResponse(
            201, json.dumps({})
        )
        self.mock_nexus_conversations_client.create_subtopic.return_value = (
            MockResponse(201, json.dumps({}))
        )
        self.mock_nexus_conversations_client.delete_topic.return_value = MockResponse(
            204, json.dumps({})
        )
        self.mock_nexus_conversations_client.delete_subtopic.return_value = (
            MockResponse(204, json.dumps({}))
        )

        # Configure flowruns query executor mocks
        self.mock_flowruns_query_executor.execute.return_value = {
            "results": [
                {"label": "label1", "value": 10, "full_value": 10},
                {"label": "label2", "value": 20, "full_value": 20},
            ],
        }

        self.mock_cache_client.get.return_value = None
        self.mock_cache_client.set.return_value = True
        self.mock_cache_client.delete.return_value = True

        self.service = ConversationsMetricsService(
            datalake_service=self.mock_datalake_service,
            nexus_conversations_client=self.mock_nexus_conversations_client,
            cache_client=self.mock_cache_client,
            flowruns_query_executor=self.mock_flowruns_query_executor,
        )
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()

    def tearDown(self) -> None:
        cache.clear()

    def test_get_csat_metrics_from_flowruns(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "csat",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        results = self.service.get_csat_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            metric_type=CsatMetricsType.HUMAN,
        )

        self.assertIn("results", results)
        self.assertIsInstance(results["results"], list)

    def test_get_csat_metrics_from_datalake(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "csat",
                },
                "operation": "recurrence",
                "op_field": "result",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        results = self.service.get_csat_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            metric_type=CsatMetricsType.AI,
        )

        self.assertIn("results", results)
        self.assertIsInstance(results["results"], list)

        totals = sum(result["full_value"] for result in results["results"])

        for result in results["results"]:
            self.assertEqual(
                result["value"], round((result["full_value"] / totals) * 100, 2)
            )

    def test_get_nps_metrics_from_flowruns(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        results = self.service.get_nps_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            metric_type=NpsMetricsType.HUMAN,
        )

        self.assertIsInstance(results, NPSMetrics)

    def test_get_nps_metrics_from_datalake(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        results = self.service.get_nps_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            metric_type=NpsMetricsType.AI,
        )

        self.assertIsInstance(results, NPSMetrics)

    def test_nps_result_transformation(self):
        results = {
            "10": 100,
            "9": 25,
            "8": 22,
            "7": 20,
            "6": 20,
            "5": 5,
            "4": 1,
            "3": 3,
            "2": 1,
            "1": 2,
            "0": 1,
        }

        expected_results = NPSMetrics(
            total_responses=200,
            promoters=NPSMetricsField(
                count=125, percentage=round(((125 / 200) * 100), 2)
            ),
            passives=NPSMetricsField(count=42, percentage=round(((42 / 200) * 100), 2)),
            detractors=NPSMetricsField(
                count=33, percentage=round(((33 / 200) * 100), 2)
            ),
            score=46.0,
        )

        transformed_results = self.service._transform_nps_results(results)

        self.assertEqual(expected_results, transformed_results)

    def test_get_topics_distribution(self):
        project = Project.objects.create(
            name="Test Project",
        )
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 2)
        topics_distribution = self.service.get_topics_distribution(
            project, start_date, end_date, ConversationType.AI
        )

        self.assertIsInstance(topics_distribution, TopicsDistributionMetrics)

    def test_get_topics(self):
        topics = self.service.get_topics(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        )

        self.assertEqual(len(topics), 1)

    def test_get_subtopics(self):
        subtopics = self.service.get_subtopics(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )

        self.assertEqual(len(subtopics), 1)

    def test_get_topics_fetches_next_pages(self):
        """Test get_topics follows next URL to fetch additional pages"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None

        page1_data = {
            "results": [{"name": "Topic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/topics/?page=2",
        }
        page2_data = {
            "results": [{"name": "Topic 2", "uuid": "bbb"}],
            "next": None,
        }

        self.mock_nexus_conversations_client.get_topics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            200, json.dumps(page2_data)
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=3):
            topics = self.service.get_topics(project_uuid)

        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]["name"], "Topic 1")
        self.assertEqual(topics[1]["name"], "Topic 2")
        self.mock_nexus_conversations_client.get_page.assert_called_once_with(
            "https://api.example.com/topics/?page=2"
        )

    @patch("insights.metrics.conversations.services.logger")
    def test_get_topics_logs_warning_when_limit_reached(self, mock_logger):
        """Test get_topics logs a warning when there are still pages after the limit"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None

        page1_data = {
            "results": [{"name": "Topic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/topics/?page=2",
        }
        page2_data = {
            "results": [{"name": "Topic 2", "uuid": "bbb"}],
            "next": "https://api.example.com/topics/?page=3",
        }

        self.mock_nexus_conversations_client.get_topics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            200, json.dumps(page2_data)
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=2):
            topics = self.service.get_topics(project_uuid)

        self.assertEqual(len(topics), 2)
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        self.assertIn("Topics pagination limit reached", warning_msg)

    def test_get_topics_no_pagination_when_next_is_null(self):
        """Test get_topics does not paginate when next is null"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None

        page1_data = {
            "results": [{"name": "Topic 1", "uuid": "aaa"}],
            "next": None,
        }

        self.mock_nexus_conversations_client.get_topics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )

        topics = self.service.get_topics(project_uuid)

        self.assertEqual(len(topics), 1)
        self.mock_nexus_conversations_client.get_page.assert_not_called()

    def test_get_topics_stops_pagination_on_error_status(self):
        """Test get_topics stops paginating when a next page returns a non-success status"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None

        page1_data = {
            "results": [{"name": "Topic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/topics/?page=2",
        }

        self.mock_nexus_conversations_client.get_topics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            500, "Internal Server Error"
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=3):
            topics = self.service.get_topics(project_uuid)

        self.assertEqual(len(topics), 1)

    def test_get_subtopics_fetches_next_pages(self):
        """Test get_subtopics follows next URL to fetch additional pages"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")

        page1_data = {
            "results": [{"name": "Subtopic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/subtopics/?page=2",
        }
        page2_data = {
            "results": [{"name": "Subtopic 2", "uuid": "bbb"}],
            "next": None,
        }

        self.mock_nexus_conversations_client.get_subtopics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            200, json.dumps(page2_data)
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=3):
            subtopics = self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertEqual(len(subtopics), 2)
        self.assertEqual(subtopics[0]["name"], "Subtopic 1")
        self.assertEqual(subtopics[1]["name"], "Subtopic 2")
        self.mock_nexus_conversations_client.get_page.assert_called_once_with(
            "https://api.example.com/subtopics/?page=2"
        )

    @patch("insights.metrics.conversations.services.logger")
    def test_get_subtopics_logs_warning_when_limit_reached(self, mock_logger):
        """Test get_subtopics logs a warning when there are still pages after the limit"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")

        page1_data = {
            "results": [{"name": "Subtopic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/subtopics/?page=2",
        }
        page2_data = {
            "results": [{"name": "Subtopic 2", "uuid": "bbb"}],
            "next": "https://api.example.com/subtopics/?page=3",
        }

        self.mock_nexus_conversations_client.get_subtopics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            200, json.dumps(page2_data)
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=2):
            subtopics = self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertEqual(len(subtopics), 2)
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        self.assertIn("Subtopics pagination limit reached", warning_msg)

    def test_get_subtopics_no_pagination_when_next_is_null(self):
        """Test get_subtopics does not paginate when next is null"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")

        page1_data = {
            "results": [{"name": "Subtopic 1", "uuid": "aaa"}],
            "next": None,
        }

        self.mock_nexus_conversations_client.get_subtopics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )

        subtopics = self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertEqual(len(subtopics), 1)
        self.mock_nexus_conversations_client.get_page.assert_not_called()

    def test_get_subtopics_stops_pagination_on_error_status(self):
        """Test get_subtopics stops paginating when a next page returns a non-success status"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")

        page1_data = {
            "results": [{"name": "Subtopic 1", "uuid": "aaa"}],
            "next": "https://api.example.com/subtopics/?page=2",
        }

        self.mock_nexus_conversations_client.get_subtopics.return_value = MockResponse(
            200, json.dumps(page1_data)
        )
        self.mock_nexus_conversations_client.get_page.return_value = MockResponse(
            500, "Internal Server Error"
        )

        with self.settings(NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES=3):
            subtopics = self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertEqual(len(subtopics), 1)

    def test_create_topic(self):
        self.service.create_topic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            name="Cancelamento",
            description="Quando cliente pede para cancelar um pedido",
        )

    def test_create_subtopic(self):
        self.service.create_subtopic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            name="Cancelamento",
            description="Quando cliente pede para cancelar um pedido",
        )

    def test_delete_topic(self):
        self.service.delete_topic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )

    def test_delete_subtopic(self):
        self.service.delete_subtopic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            subtopic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )

    def test_get_totals(self):
        totals = self.service.get_totals(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(totals, ConversationsTotalsMetrics)

    def test_get_generic_metrics_by_key(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                    "key": "test_key",
                },
            },
        )
        metrics = self.service.get_generic_metrics_by_key(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(metrics, dict)

    def test_cannot_get_generic_metrics_by_key_without_agent_uuid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "key": "test_key",
                },
            },
        )

        with self.assertRaises(ConversationsMetricsError):
            self.service.get_generic_metrics_by_key(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_cannot_get_generic_metrics_by_key_without_key(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        with self.assertRaises(ConversationsMetricsError):
            self.service.get_generic_metrics_by_key(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    @patch(
        "insights.metrics.conversations.services.is_feature_active_for_attributes",
        return_value=False,
    )
    def test_get_sales_funnel_data(self, mock_feature_flag):
        self.mock_datalake_service.get_sales_funnel_data.return_value = SalesFunnelData(
            leads_count=100,
            total_orders_count=100,
            total_orders_value=10000,
            currency_code="BRL",
        )
        metrics = self.service.get_sales_funnel_data(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(metrics, SalesFunnelMetrics)

        self.mock_datalake_service.get_sales_funnel_data.assert_called_once_with(
            self.project.uuid,
            self.start_date,
            self.end_date,
        )
        self.mock_datalake_service.get_sales_funnel_data_parallel.assert_not_called()

        self.assertEqual(metrics.leads_count, 100)
        self.assertEqual(metrics.total_orders_count, 100)
        self.assertEqual(metrics.total_orders_value, 10000)
        self.assertEqual(metrics.currency_code, "BRL")

    @patch(
        "insights.metrics.conversations.services.is_feature_active_for_attributes",
        return_value=True,
    )
    def test_get_sales_funnel_data_uses_parallel_when_feature_flag_active(
        self, mock_feature_flag
    ):
        self.mock_datalake_service.get_sales_funnel_data_parallel.return_value = (
            SalesFunnelData(
                leads_count=100,
                total_orders_count=100,
                total_orders_value=10000,
                currency_code="BRL",
            )
        )
        metrics = self.service.get_sales_funnel_data(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(metrics, SalesFunnelMetrics)

        mock_feature_flag.assert_called_once_with(
            key="insightsSalesFunnelUseParallelProcessing",
            attributes={"projectUUID": self.project.uuid},
        )
        self.mock_datalake_service.get_sales_funnel_data_parallel.assert_called_once_with(
            self.project.uuid,
            self.start_date,
            self.end_date,
        )
        self.mock_datalake_service.get_sales_funnel_data.assert_not_called()

        self.assertEqual(metrics.leads_count, 100)
        self.assertEqual(metrics.total_orders_count, 100)
        self.assertEqual(metrics.total_orders_value, 10000)
        self.assertEqual(metrics.currency_code, "BRL")

    @patch(
        "insights.metrics.conversations.services.is_feature_active_for_attributes",
        side_effect=Exception("GrowthBook connection error"),
    )
    def test_get_sales_funnel_data_falls_back_to_sequential_on_feature_flag_error(
        self, mock_feature_flag
    ):
        self.mock_datalake_service.get_sales_funnel_data.return_value = SalesFunnelData(
            leads_count=50,
            total_orders_count=10,
            total_orders_value=5000,
            currency_code="USD",
        )
        metrics = self.service.get_sales_funnel_data(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(metrics, SalesFunnelMetrics)

        self.mock_datalake_service.get_sales_funnel_data.assert_called_once_with(
            self.project.uuid,
            self.start_date,
            self.end_date,
        )
        self.mock_datalake_service.get_sales_funnel_data_parallel.assert_not_called()

        self.assertEqual(metrics.leads_count, 50)
        self.assertEqual(metrics.total_orders_count, 10)
        self.assertEqual(metrics.total_orders_value, 5000)
        self.assertEqual(metrics.currency_code, "USD")

    def test_check_if_sales_funnel_data_exists_when_data_does_not_exist(self):
        self.mock_datalake_service.check_if_sales_funnel_data_exists.return_value = (
            False
        )
        results = self.service.check_if_sales_funnel_data_exists(self.project.uuid)
        self.assertFalse(results)

    def test_check_if_sales_funnel_data_exists_when_data_exists(self):
        self.mock_datalake_service.check_if_sales_funnel_data_exists.return_value = True
        results = self.service.check_if_sales_funnel_data_exists(self.project.uuid)
        self.assertTrue(results)

    def test_get_available_widgets(self):
        self.mock_datalake_service.check_if_sales_funnel_data_exists.return_value = True
        available_widgets = self.service.get_available_widgets(self.project)

        self.assertIsInstance(available_widgets, AvailableWidgetsList)
        self.assertEqual(
            available_widgets.available_widgets, [AvailableWidgets.SALES_FUNNEL]
        )

    def test_get_available_widgets_with_native_type(self):
        self.mock_datalake_service.check_if_sales_funnel_data_exists.return_value = True
        available_widgets = self.service.get_available_widgets(
            self.project, AvailableWidgetsListType.NATIVE
        )

        self.assertIsInstance(available_widgets, AvailableWidgetsList)
        self.assertEqual(
            available_widgets.available_widgets, [AvailableWidgets.SALES_FUNNEL]
        )

    def test_get_available_widgets_with_custom_type(self):
        self.mock_datalake_service.check_if_sales_funnel_data_exists.return_value = True
        available_widgets = self.service.get_available_widgets(
            self.project, AvailableWidgetsListType.CUSTOM
        )

        self.assertIsInstance(available_widgets, AvailableWidgetsList)
        self.assertEqual(available_widgets.available_widgets, [])

    def test_get_crosstab_data_when_widget_type_is_invalid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="invalid",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_crosstab_data(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

        self.assertEqual(str(context.exception), "Widget type or source is not valid")

    def test_get_crosstab_data_when_widget_source_is_invalid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="invalid",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_crosstab_data(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

        self.assertEqual(str(context.exception), "Widget type or source is not valid")

    def test_get_crosstab_data_when_source_a_is_invalid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {},
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_crosstab_data(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

        self.assertEqual(str(context.exception), "Key is required")

    def test_get_crosstab_data_when_source_b_is_invalid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {},
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_crosstab_data(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

        self.assertEqual(str(context.exception), "Key is required")

    def test_get_crosstab_data(self):
        self.mock_datalake_service.get_crosstab_data.return_value = {
            "Delivery": {
                "Satisfied": 10,
                "Unsatisfied": 10,
            },
            "Shopping": {
                "Satisfied": 10,
                "Unsatisfied": 10,
            },
        }

        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        data = self.service.get_crosstab_data(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(
            data,
            [
                CrosstabItemData(
                    title="Delivery",
                    total=20,
                    subitems=[
                        CrosstabSubItemData(
                            title="Satisfied",
                            count=10,
                            percentage=50,
                        ),
                        CrosstabSubItemData(
                            title="Unsatisfied",
                            count=10,
                            percentage=50,
                        ),
                    ],
                ),
                CrosstabItemData(
                    title="Shopping",
                    total=20,
                    subitems=[
                        CrosstabSubItemData(
                            title="Satisfied",
                            count=10,
                            percentage=50,
                        ),
                        CrosstabSubItemData(
                            title="Unsatisfied",
                            count=10,
                            percentage=50,
                        ),
                    ],
                ),
            ],
        )

    def test_get_agent_invocations(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())

        self.mock_datalake_service.get_agent_invocations.return_value = {
            "invocation_1": AgentInvocationMetric(
                agent_uuid=agent_uuid,
                count=10,
            )
        }

        results = self.service.get_agent_invocations(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(results, AgentInvocationMetrics)
        self.assertEqual(results.total, 1)
        self.assertEqual(len(results.invocations), 1)
        self.assertIsInstance(results.invocations[0], AgentInvocationItem)
        self.assertEqual(results.invocations[0].label, "invocation_1")
        self.assertEqual(
            results.invocations[0].agent, AgentInvocationAgent(uuid=agent_uuid)
        )
        self.assertEqual(results.invocations[0].value, 100.0)
        self.assertEqual(results.invocations[0].full_value, 10)

        self.mock_datalake_service.get_agent_invocations.assert_called_once_with(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def test_get_agent_invocations_with_none_agent_uuid(self):
        project_uuid = uuid.uuid4()

        self.mock_datalake_service.get_agent_invocations.return_value = {
            "invocation_1": AgentInvocationMetric(
                agent_uuid=None,
                count=10,
            )
        }

        results = self.service.get_agent_invocations(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(results, AgentInvocationMetrics)
        self.assertEqual(results.total, 1)
        self.assertEqual(len(results.invocations), 1)
        self.assertIsInstance(results.invocations[0], AgentInvocationItem)
        self.assertEqual(results.invocations[0].label, "invocation_1")
        self.assertIsNone(results.invocations[0].agent)
        self.assertEqual(results.invocations[0].value, 100.0)
        self.assertEqual(results.invocations[0].full_value, 10)

        self.mock_datalake_service.get_agent_invocations.assert_called_once_with(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def test_get_agent_invocations_empty_result(self):
        self.mock_datalake_service.get_agent_invocations.return_value = {}

        results = self.service.get_agent_invocations(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(results, AgentInvocationMetrics)
        self.assertEqual(results.invocations, [])
        self.assertEqual(results.total, 0)

    def test_get_agent_invocations_multiple_agents(self):
        agent_uuid_1 = str(uuid.uuid4())
        agent_uuid_2 = str(uuid.uuid4())

        self.mock_datalake_service.get_agent_invocations.return_value = {
            "invocation_1": AgentInvocationMetric(
                agent_uuid=agent_uuid_1,
                count=10,
            ),
            "invocation_2": AgentInvocationMetric(
                agent_uuid=agent_uuid_2,
                count=20,
            ),
        }

        results = self.service.get_agent_invocations(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(results.total, 2)
        self.assertEqual(len(results.invocations), 2)
        self.assertEqual(results.invocations[0].label, "invocation_1")
        self.assertEqual(results.invocations[0].full_value, 10)
        self.assertEqual(results.invocations[0].value, 33.33)
        self.assertEqual(results.invocations[1].label, "invocation_2")
        self.assertEqual(results.invocations[1].full_value, 20)
        self.assertEqual(results.invocations[1].value, 66.67)

    def test_get_agent_invocations_mixed_agent_uuids(self):
        agent_uuid_1 = str(uuid.uuid4())

        self.mock_datalake_service.get_agent_invocations.return_value = {
            "invocation_1": AgentInvocationMetric(
                agent_uuid=agent_uuid_1,
                count=10,
            ),
            "invocation_2": AgentInvocationMetric(
                agent_uuid=None,
                count=20,
            ),
        }

        results = self.service.get_agent_invocations(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(results.total, 2)
        self.assertEqual(len(results.invocations), 2)
        self.assertEqual(results.invocations[0].label, "invocation_1")
        self.assertEqual(
            results.invocations[0].agent, AgentInvocationAgent(uuid=agent_uuid_1)
        )
        self.assertEqual(results.invocations[0].full_value, 10)
        self.assertEqual(results.invocations[1].label, "invocation_2")
        self.assertIsNone(results.invocations[1].agent)
        self.assertEqual(results.invocations[1].full_value, 20)

    def test_get_agent_invocations_propagates_exception(self):
        self.mock_datalake_service.get_agent_invocations.side_effect = Exception(
            "Datalake error"
        )

        with self.assertRaises(Exception):
            self.service.get_agent_invocations(
                project_uuid=uuid.uuid4(),
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_tool_results(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())

        self.mock_datalake_service.get_tool_results.return_value = {
            "tool_result_1": ToolResultMetric(
                agent_uuid=agent_uuid,
                count=10,
            )
        }

        results = self.service.get_tool_results(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(results, ToolResultMetrics)
        self.assertEqual(results.total, 1)
        self.assertEqual(len(results.tool_results), 1)
        self.assertIsInstance(results.tool_results[0], ToolResultItem)
        self.assertEqual(results.tool_results[0].label, "tool_result_1")
        self.assertEqual(
            results.tool_results[0].agent, ToolResultAgent(uuid=agent_uuid)
        )
        self.assertEqual(results.tool_results[0].value, 100.0)
        self.assertEqual(results.tool_results[0].full_value, 10)

        self.mock_datalake_service.get_tool_results.assert_called_once_with(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def test_get_tool_results_with_none_agent_uuid(self):
        project_uuid = uuid.uuid4()

        self.mock_datalake_service.get_tool_results.return_value = {
            "tool_result_1": ToolResultMetric(
                agent_uuid=None,
                count=10,
            )
        }
        results = self.service.get_tool_results(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(results, ToolResultMetrics)
        self.assertEqual(results.total, 1)
        self.assertEqual(len(results.tool_results), 1)
        self.assertIsInstance(results.tool_results[0], ToolResultItem)
        self.assertEqual(results.tool_results[0].label, "tool_result_1")
        self.assertIsNone(results.tool_results[0].agent)
        self.assertEqual(results.tool_results[0].value, 100.0)
        self.assertEqual(results.tool_results[0].full_value, 10)

        self.mock_datalake_service.get_tool_results.assert_called_once_with(
            project_uuid=project_uuid,
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def test_get_tool_results_empty_result(self):
        self.mock_datalake_service.get_tool_results.return_value = {}

        results = self.service.get_tool_results(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(results, ToolResultMetrics)
        self.assertEqual(results.tool_results, [])
        self.assertEqual(results.total, 0)

    def test_get_tool_results_multiple_agents(self):
        agent_uuid_1 = str(uuid.uuid4())
        agent_uuid_2 = str(uuid.uuid4())

        self.mock_datalake_service.get_tool_results.return_value = {
            "tool_result_1": ToolResultMetric(
                agent_uuid=agent_uuid_1,
                count=10,
            ),
            "tool_result_2": ToolResultMetric(
                agent_uuid=agent_uuid_2,
                count=20,
            ),
        }

        results = self.service.get_tool_results(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(results.total, 2)
        self.assertEqual(len(results.tool_results), 2)
        self.assertEqual(results.tool_results[0].label, "tool_result_1")
        self.assertEqual(results.tool_results[0].full_value, 10)
        self.assertEqual(results.tool_results[0].value, 33.33)
        self.assertEqual(results.tool_results[1].label, "tool_result_2")
        self.assertEqual(results.tool_results[1].full_value, 20)
        self.assertEqual(results.tool_results[1].value, 66.67)

    def test_get_tool_results_mixed_agent_uuids(self):
        agent_uuid_1 = str(uuid.uuid4())

        self.mock_datalake_service.get_tool_results.return_value = {
            "tool_result_1": ToolResultMetric(
                agent_uuid=agent_uuid_1,
                count=10,
            ),
            "tool_result_2": ToolResultMetric(
                agent_uuid=None,
                count=20,
            ),
        }

        results = self.service.get_tool_results(
            project_uuid=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(results.total, 2)
        self.assertEqual(len(results.tool_results), 2)
        self.assertEqual(results.tool_results[0].label, "tool_result_1")
        self.assertEqual(
            results.tool_results[0].agent, ToolResultAgent(uuid=agent_uuid_1)
        )
        self.assertEqual(results.tool_results[0].full_value, 10)
        self.assertEqual(results.tool_results[1].label, "tool_result_2")
        self.assertIsNone(results.tool_results[1].agent)
        self.assertEqual(results.tool_results[1].full_value, 20)

    def test_get_tool_results_propagates_exception(self):
        self.mock_datalake_service.get_tool_results.side_effect = Exception(
            "Datalake error"
        )

        with self.assertRaises(Exception):
            self.service.get_tool_results(
                project_uuid=uuid.uuid4(),
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_topics_with_cache_hit(self):
        """Test get_topics when cache is hit"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        cached_data = json.dumps([{"name": "Cached Topic", "uuid": "123"}])
        self.mock_cache_client.get.return_value = cached_data

        topics = self.service.get_topics(project_uuid)

        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0]["name"], "Cached Topic")
        self.mock_nexus_conversations_client.get_topics.assert_not_called()

    def test_get_topics_with_exception(self):
        """Test get_topics when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None
        self.mock_nexus_conversations_client.get_topics.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_topics(project_uuid)

        self.assertIn("Error fetching topics", str(context.exception))

    def test_get_topics_with_non_success_status(self):
        """Test get_topics when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_cache_client.get.return_value = None
        mock_response = MockResponse(500, "Internal Server Error")
        self.mock_nexus_conversations_client.get_topics.return_value = mock_response

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_topics(project_uuid)

        self.assertIn("Error fetching topics", str(context.exception))

    def test_get_subtopics_with_exception(self):
        """Test get_subtopics when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_nexus_conversations_client.get_subtopics.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertIn("Error fetching subtopics", str(context.exception))

    def test_get_subtopics_with_non_success_status(self):
        """Test get_subtopics when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(404, "Not Found")
        self.mock_nexus_conversations_client.get_subtopics.return_value = mock_response

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_subtopics(project_uuid, topic_uuid)

        self.assertIn("Error fetching topics", str(context.exception))

    def test_create_topic_with_exception(self):
        """Test create_topic when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_nexus_conversations_client.create_topic.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.create_topic(project_uuid, "Test Topic", "Test Description")

        self.assertIn("Error creating topic", str(context.exception))

    def test_create_topic_with_json_parse_error(self):
        """Test create_topic when response.json() fails"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(201, "invalid json")
        mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))
        self.mock_nexus_conversations_client.create_topic.return_value = mock_response

        result = self.service.create_topic(
            project_uuid, "Test Topic", "Test Description"
        )

        self.assertEqual(result, "invalid json")

    def test_create_topic_with_non_success_status(self):
        """Test create_topic when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(400, "Bad Request")
        self.mock_nexus_conversations_client.create_topic.return_value = mock_response

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.create_topic(project_uuid, "Test Topic", "Test Description")

        self.assertIn("Error creating topic", str(context.exception))

    def test_create_subtopic_with_exception(self):
        """Test create_subtopic when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_nexus_conversations_client.create_subtopic.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.create_subtopic(
                project_uuid, topic_uuid, "Test Subtopic", "Test Description"
            )

        self.assertIn("Error creating subtopic", str(context.exception))

    def test_create_subtopic_with_json_parse_error(self):
        """Test create_subtopic when response.json() fails"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(201, "invalid json")
        mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))
        self.mock_nexus_conversations_client.create_subtopic.return_value = (
            mock_response
        )

        result = self.service.create_subtopic(
            project_uuid, topic_uuid, "Test Subtopic", "Test Description"
        )

        self.assertEqual(result, "invalid json")

    def test_create_subtopic_with_non_success_status(self):
        """Test create_subtopic when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(400, "Bad Request")
        self.mock_nexus_conversations_client.create_subtopic.return_value = (
            mock_response
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.create_subtopic(
                project_uuid, topic_uuid, "Test Subtopic", "Test Description"
            )

        self.assertIn("Error creating subtopic", str(context.exception))

    def test_delete_topic_with_exception(self):
        """Test delete_topic when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_nexus_conversations_client.delete_topic.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.delete_topic(project_uuid, topic_uuid)

        self.assertIn("Error deleting topic", str(context.exception))

    def test_delete_topic_with_non_success_status(self):
        """Test delete_topic when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(404, "Not Found")
        self.mock_nexus_conversations_client.delete_topic.return_value = mock_response

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.delete_topic(project_uuid, topic_uuid)

        self.assertIn("Error deleting topic", str(context.exception))

    def test_delete_subtopic_with_exception(self):
        """Test delete_subtopic when nexus client raises exception"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        subtopic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        self.mock_nexus_conversations_client.delete_subtopic.side_effect = Exception(
            "Network error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.delete_subtopic(project_uuid, topic_uuid, subtopic_uuid)

        self.assertIn("Error deleting subtopic", str(context.exception))

    def test_delete_subtopic_with_non_success_status(self):
        """Test delete_subtopic when response status is not success"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        topic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        subtopic_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        mock_response = MockResponse(404, "Not Found")
        self.mock_nexus_conversations_client.delete_subtopic.return_value = (
            mock_response
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.delete_subtopic(project_uuid, topic_uuid, subtopic_uuid)

        self.assertIn("Error deleting subtopic", str(context.exception))

    def test_get_topics_distribution_with_exception(self):
        """Test get_topics_distribution when datalake service raises exception"""
        project = Project.objects.create(name="Test Project")
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 2)

        self.mock_datalake_service.get_topics_distribution.side_effect = Exception(
            "Datalake error"
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_topics_distribution(
                project, start_date, end_date, ConversationType.AI
            )

        self.assertIn("Failed to get topics distribution", str(context.exception))

    def test_get_csat_metrics_missing_flow_uuid(self):
        """Test get_csat_metrics when flow_uuid is missing"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {},
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_csat_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=CsatMetricsType.HUMAN,
            )

        self.assertIn("Flow UUID is required", str(context.exception))

    def test_get_csat_metrics_missing_op_field(self):
        """Test get_csat_metrics when op_field is missing"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                },
                "operation": "recurrence",
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_csat_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=CsatMetricsType.HUMAN,
            )

        self.assertIn("Op field is required", str(context.exception))

    def test_get_csat_metrics_missing_agent_uuid(self):
        """Test get_csat_metrics when agent_uuid is missing for AI type"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "datalake_config": {},
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_csat_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=CsatMetricsType.AI,
            )

        self.assertIn("Agent UUID is required", str(context.exception))

    def test_get_nps_metrics_missing_flow_uuid(self):
        """Test get_nps_metrics when flow_uuid is missing"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {},
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_nps_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=NpsMetricsType.HUMAN,
            )

        self.assertIn("Flow UUID is required", str(context.exception))

    def test_get_nps_metrics_missing_op_field(self):
        """Test get_nps_metrics when op_field is missing"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                },
                "operation": "recurrence",
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_nps_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=NpsMetricsType.HUMAN,
            )

        self.assertIn("Op field is required", str(context.exception))

    def test_get_nps_metrics_missing_agent_uuid(self):
        """Test get_nps_metrics when agent_uuid is missing for AI type"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "datalake_config": {},
            },
        )

        with self.assertRaises(ConversationsMetricsError) as context:
            self.service.get_nps_metrics(
                project_uuid=self.project.uuid,
                widget=widget,
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                metric_type=NpsMetricsType.AI,
            )

        self.assertIn("Agent UUID is required", str(context.exception))

    def test_convert_to_iso_string_with_datetime(self):
        """Test _convert_to_iso_string with datetime object"""
        test_datetime = datetime(2026, 1, 15, 10, 30, 0)
        result = self.service._convert_to_iso_string(test_datetime)
        self.assertEqual(result, "2026-01-15T10:30:00")
        self.assertIsInstance(result, str)

    def test_convert_to_iso_string_with_string(self):
        """Test _convert_to_iso_string with string already in ISO format"""
        test_string = "2026-01-15T10:30:00"
        result = self.service._convert_to_iso_string(test_string)
        self.assertEqual(result, test_string)
        self.assertIsInstance(result, str)

    def test_csat_metrics_uses_correct_filters(self):
        """Test that CSAT metrics uses __ syntax for date filters"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {"flow": "test-flow-uuid"},
                "op_field": "csat_score",
            },
        )

        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)

        self.service.get_csat_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=start_date,
            end_date=end_date,
            metric_type=CsatMetricsType.HUMAN,
        )

        # Verify the executor was called with correct filter format
        call_args = self.mock_flowruns_query_executor.execute.call_args
        filters = call_args[0][0]

        self.assertIn("created_on__gte", filters)
        self.assertIn("created_on__lte", filters)
        self.assertNotIn("created_on", filters)
        self.assertEqual(filters["created_on__gte"], "2026-01-15T00:00:00")
        self.assertEqual(filters["created_on__lte"], "2026-01-22T00:00:00")

    def test_nps_metrics_uses_correct_filters(self):
        """Test that NPS metrics uses __ syntax for date filters"""
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {"flow": "test-flow-uuid"},
                "op_field": "nps_score",
            },
        )

        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)

        self.service.get_nps_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=start_date,
            end_date=end_date,
            metric_type=NpsMetricsType.HUMAN,
        )

        # Verify the executor was called with correct filter format
        call_args = self.mock_flowruns_query_executor.execute.call_args
        filters = call_args[0][0]

        self.assertIn("created_on__gte", filters)
        self.assertIn("created_on__lte", filters)
        self.assertNotIn("created_on", filters)
        self.assertEqual(filters["created_on__gte"], "2026-01-15T00:00:00")
        self.assertEqual(filters["created_on__lte"], "2026-01-22T00:00:00")

    def test_get_event_count(self):
        """Test get_event_count"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        event_name = "test_event"
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)
        key = "test_key"
        agent_uuid = "test_agent_uuid"

        self.mock_datalake_service.get_event_count.return_value = 10

        count = self.service.get_event_count(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )

        self.assertEqual(count, 10)

    def test_get_events_values_sum(self):
        """Test get_events_values_sum"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        event_name = "test_event"
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)
        key = "test_key"
        agent_uuid = "test_agent_uuid"
        self.mock_datalake_service.get_events_values_sum.return_value = 10
        sum_result = self.service.get_events_values_sum(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )
        self.assertEqual(sum_result, 10)

    def test_get_events_values_average(self):
        """Test get_events_values_average"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        event_name = "test_event"
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)
        key = "test_key"
        agent_uuid = "test_agent_uuid"
        self.mock_datalake_service.get_events_values_average.return_value = 10
        average = self.service.get_events_values_average(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )

        self.assertEqual(average, 10)

    def test_get_events_highest_value(self):
        """Test get_events_highest_value"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        event_name = "test_event"
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)
        key = "test_key"
        agent_uuid = "test_agent_uuid"
        self.mock_datalake_service.get_events_highest_value.return_value = 10
        highest_value = self.service.get_events_highest_value(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )
        self.assertEqual(highest_value, 10)

    def test_get_events_lowest_value(self):
        """Test get_events_lowest_value"""
        project_uuid = UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        event_name = "test_event"
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 1, 22, 0, 0, 0)
        key = "test_key"
        agent_uuid = "test_agent_uuid"

        self.mock_datalake_service.get_events_lowest_value.return_value = 10
        lowest_value = self.service.get_events_lowest_value(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )
        self.assertEqual(lowest_value, 10)

    def test_get_absolute_numbers(self):
        agent_uuid = str(uuid.uuid4())
        parent = Widget.objects.create(
            name="Test Parent Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={},
        )
        widget = Widget.objects.create(
            name="Test Widget",
            parent=parent,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={
                "operation": AbsoluteNumbersMetricsType.TOTAL,
                "key": "test_key",
                "agent_uuid": agent_uuid,
            },
        )

        mock_method = Mock(return_value=42)
        self.service._get_absolute_numbers_method_by_operation = Mock(
            return_value=mock_method
        )

        result = self.service.get_absolute_numbers(
            widget=widget,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(result.value, 42)
        self.service._get_absolute_numbers_method_by_operation.assert_called_once_with(
            AbsoluteNumbersMetricsType.TOTAL
        )
        mock_method.assert_called_once_with(
            project_uuid=parent.dashboard.project_id,
            key="test_key",
            start_date=self.start_date,
            end_date=self.end_date,
            agent_uuid=agent_uuid,
            field_name=None,
            event_name="weni_nexus_data",
        )

    def test_get_absolute_numbers_each_operation_type(self):
        parent = Widget.objects.create(
            name="Test Parent Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={},
        )

        for operation in AbsoluteNumbersMetricsType:
            agent_uuid = str(uuid.uuid4())
            widget = Widget.objects.create(
                name="Test Widget",
                parent=parent,
                source="conversations.absolute_numbers.child",
                type="absolute_numbers",
                position=[1, 2],
                config={
                    "operation": operation,
                    "key": "test_key",
                    "agent_uuid": agent_uuid,
                },
            )

            mock_method = Mock(return_value=99)
            self.service._get_absolute_numbers_method_by_operation = Mock(
                return_value=mock_method
            )

            result = self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

            self.assertEqual(result.value, 99)
            self.service._get_absolute_numbers_method_by_operation.assert_called_once_with(
                operation
            )

    def test_get_absolute_numbers_missing_operation(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={
                "key": "test_key",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        with self.assertRaises(AssertionError):
            self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_absolute_numbers_missing_key(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={
                "operation": AbsoluteNumbersMetricsType.TOTAL,
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        with self.assertRaises(AssertionError):
            self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_absolute_numbers_missing_agent_uuid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={
                "operation": AbsoluteNumbersMetricsType.TOTAL,
                "key": "test_key",
                "datalake_config": {},
            },
        )

        with self.assertRaises(AssertionError):
            self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_absolute_numbers_missing_datalake_config(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={
                "operation": AbsoluteNumbersMetricsType.TOTAL,
                "key": "test_key",
            },
        )

        with self.assertRaises(AssertionError):
            self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )

    def test_get_absolute_numbers_empty_config(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers",
            type="absolute_numbers",
            position=[1, 2],
            config={},
        )

        with self.assertRaises(AssertionError):
            self.service.get_absolute_numbers(
                widget=widget,
                start_date=self.start_date,
                end_date=self.end_date,
            )
