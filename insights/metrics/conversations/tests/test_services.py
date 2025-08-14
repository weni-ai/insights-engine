from datetime import datetime, timedelta
from unittest.mock import patch
import uuid
from uuid import UUID

from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone

from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.widgets.models import Widget

from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    QueueMetric,
    RoomsByQueueMetric,
    SubjectMetricData,
    SubjectsMetrics,
    TopicsDistributionMetrics,
    NPSMetrics,
)
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)
from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockDatalakeConversationsMetricsService,
)
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):

    def setUp(self):
        cache.clear()
        self.project = Project.objects.create(name="Test Project")
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.service = ConversationsMetricsService(
            datalake_service=MockDatalakeConversationsMetricsService(),
            nexus_client=MockNexusClient(),
            flowruns_query_executor=MockFlowRunsQueryExecutor,
        )

    def test_get_timeseries_for_day_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.DAY,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "total"
            ],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "by_human"
            ],
        )

    def test_get_timeseries_for_hour_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.HOUR,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["by_human"],
        )

    def test_get_timeseries_for_month_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.MONTH,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["by_human"],
        )

    def test_get_subjects_metrics(self):
        subjects_metrics = self.service.get_subjects_metrics(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
            conversation_type=ConversationsSubjectsType.GENERAL,
        )

        self.assertIsInstance(subjects_metrics, SubjectsMetrics)
        self.assertEqual(subjects_metrics.has_more, False)

        subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])

        self.assertEqual(len(subjects_metrics.subjects), len(subjects_data))

        for i, subject in enumerate(subjects_metrics.subjects):
            self.assertIsInstance(subject, SubjectMetricData)
            subject_data = subjects_data[i]

            self.assertEqual(
                subject.name,
                subject_data.get("name"),
            )
            self.assertEqual(
                subject.percentage,
                subject_data.get("percentage"),
            )

    def test_get_subjects_metrics_with_limit(self):
        subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])

        subjects_metrics = self.service.get_subjects_metrics(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
            conversation_type=ConversationsSubjectsType.GENERAL,
            limit=len(subjects_data) - 1,
        )

        self.assertIsInstance(subjects_metrics, SubjectsMetrics)
        self.assertEqual(subjects_metrics.has_more, True)

        self.assertEqual(len(subjects_metrics.subjects), len(subjects_data) - 1)

        for i, subject in enumerate(subjects_metrics.subjects):
            self.assertIsInstance(subject, SubjectMetricData)
            subject_data = subjects_data[i]

            self.assertEqual(
                subject.name,
                subject_data.get("name"),
            )
            self.assertEqual(
                subject.percentage,
                subject_data.get("percentage"),
            )

        self.project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project=self.project,
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date(),
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                    QueueMetric(name="Test Queue 2", percentage=66.67),
                ],
                has_more=False,
            ),
        )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue_with_limit(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project=self.project,
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date(),
            limit=1,
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                ],
                has_more=True,
            ),
        )

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
