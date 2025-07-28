from datetime import datetime, timedelta
import uuid
from uuid import UUID
from django.test import TestCase
from django.core.cache import cache

from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetrics,
    NPSMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.widgets.models import Widget


class TestConversationsMetricsService(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.service = ConversationsMetricsService(
            datalake_service=MockDatalakeConversationsMetricsService(),
            nexus_client=MockNexusClient(),
            flowruns_query_executor=MockFlowRunsQueryExecutor,
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
            promoters=125,
            passives=42,
            detractors=33,
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
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(totals, ConversationsTotalsMetrics)
