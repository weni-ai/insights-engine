from datetime import datetime, time
import uuid
from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType, CsatMetricsType
from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    CsatMetricsQueryParamsSerializer,
    SubtopicSerializer,
    TopicSerializer,
    TopicsDistributionMetricsQueryParamsSerializer,
    TopicsDistributionMetricsSerializer,
)
from insights.widgets.models import Widget


class TestConversationBaseQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("project", serializer.validated_data)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)

        # Test that start_date is converted to datetime at midnight
        start_date = serializer.validated_data["start_date"]
        self.assertIsInstance(start_date, datetime)
        self.assertIsNotNone(start_date.tzinfo)  # Should be timezone-aware
        self.assertEqual(start_date.time(), time.min)  # Should be 00:00:00
        self.assertEqual(start_date.date().isoformat(), "2021-01-01")

        # Test that end_date is converted to datetime at 23:59:59
        end_date = serializer.validated_data["end_date"]
        self.assertIsInstance(end_date, datetime)
        self.assertIsNotNone(end_date.tzinfo)  # Should be timezone-aware
        self.assertEqual(end_date.time(), time(23, 59, 59))  # Should be 23:59:59
        self.assertEqual(end_date.date().isoformat(), "2021-01-02")

    def test_serializer_with_timezone(self):
        # Create a project with a specific timezone
        project_with_tz = Project.objects.create(
            name="Test Project with TZ", timezone="America/New_York"
        )

        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": project_with_tz.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Check that timezone is correctly applied
        self.assertEqual(str(start_date.tzinfo), "America/New_York")
        self.assertEqual(str(end_date.tzinfo), "America/New_York")

        # Check times are correct
        self.assertEqual(start_date.time(), time.min)
        self.assertEqual(end_date.time(), time(23, 59, 59))

    def test_serializer_without_timezone(self):
        # Create a project without timezone (should default to UTC)
        project_no_tz = Project.objects.create(name="Test Project No TZ", timezone="")

        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": project_no_tz.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Check that UTC timezone is applied when no timezone is set
        self.assertEqual(str(start_date.tzinfo), "UTC")
        self.assertEqual(str(end_date.tzinfo), "UTC")

    def test_serializer_invalid_start_date(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestCsatMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.widget = Widget.objects.create(
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

    def test_serializer(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": self.widget.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": CsatMetricsType.HUMAN,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(
            str(serializer.validated_data["start_date"]), "2021-01-01 00:00:00+00:00"
        )
        self.assertEqual(
            str(serializer.validated_data["end_date"]), "2021-01-02 23:59:59+00:00"
        )
        self.assertEqual(serializer.validated_data["type"], CsatMetricsType.HUMAN)
        self.assertEqual(serializer.validated_data["widget"], self.widget)

    def test_serializer_invalid_type(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": self.widget.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": "invalid",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")

    def test_serializer_invalid_widget_uuid(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": uuid.uuid4(),
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": CsatMetricsType.HUMAN,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("widget_uuid", serializer.errors)
        self.assertEqual(serializer.errors["widget_uuid"][0].code, "widget_not_found")


class TestTopicsDistributionMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = TopicsDistributionMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "type": ConversationType.AI,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("project", serializer.validated_data)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(
            str(serializer.validated_data["start_date"]), "2021-01-01 00:00:00+00:00"
        )
        self.assertEqual(
            str(serializer.validated_data["end_date"]), "2021-01-02 23:59:59+00:00"
        )

    def test_serializer_invalid_start_date(self):
        serializer = TopicsDistributionMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
                "type": ConversationType.AI,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = TopicsDistributionMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "type": ConversationType.AI,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestSubtopicSerializer(TestCase):
    def test_serializer(self):
        subtopic = SubtopicMetrics(
            uuid=uuid.uuid4(),
            name="Test Subtopic",
            percentage=100,
            quantity=1,
        )
        serializer = SubtopicSerializer(subtopic)
        self.assertEqual(serializer.data["name"], "Test Subtopic")
        self.assertEqual(serializer.data["quantity"], 1)
        self.assertEqual(serializer.data["percentage"], 100)


class TestTopicSerializer(TestCase):
    def test_serializer(self):
        topic = TopicMetrics(
            uuid=uuid.uuid4(),
            name="Test Topic",
            quantity=1,
            percentage=100,
            subtopics=[
                SubtopicMetrics(
                    uuid=uuid.uuid4(),
                    name="Test Subtopic",
                    quantity=1,
                    percentage=100,
                )
            ],
        )
        serializer = TopicSerializer(topic)
        self.assertEqual(serializer.data["uuid"], str(topic.uuid))
        self.assertEqual(serializer.data["name"], "Test Topic")
        self.assertEqual(serializer.data["quantity"], 1)
        self.assertEqual(serializer.data["percentage"], 100)
        self.assertEqual(
            [
                {
                    "uuid": str(subtopic.uuid),
                    "name": subtopic.name,
                    "quantity": subtopic.quantity,
                    "percentage": subtopic.percentage,
                }
                for subtopic in topic.subtopics
            ],
            serializer.data["subtopics"],
        )


class TestTopicsDistributionMetricsSerializer(TestCase):
    def test_serializer(self):
        topics = [
            TopicMetrics(
                uuid=uuid.uuid4(),
                name="Test Topic",
                quantity=1,
                percentage=100,
                subtopics=[
                    SubtopicMetrics(
                        uuid=uuid.uuid4(),
                        name="Test Subtopic",
                        quantity=1,
                        percentage=100,
                    )
                ],
            )
        ]
        topics_distribution_metrics = TopicsDistributionMetrics(topics=topics)
        serializer = TopicsDistributionMetricsSerializer(topics_distribution_metrics)
        for topic_data, topic in zip(serializer.data["topics"], topics):
            self.assertEqual(topic_data["uuid"], str(topic.uuid))
            self.assertEqual(topic_data["name"], topic.name)
            self.assertEqual(topic_data["quantity"], topic.quantity)
            self.assertEqual(topic_data["percentage"], topic.percentage)
            for subtopic_data, subtopic in zip(
                topic_data["subtopics"], topic.subtopics
            ):
                self.assertEqual(subtopic_data["uuid"], str(subtopic.uuid))
                self.assertEqual(subtopic_data["name"], subtopic.name)
                self.assertEqual(subtopic_data["quantity"], subtopic.quantity)
                self.assertEqual(subtopic_data["percentage"], subtopic.percentage)


class TestConversationTotalsMetricsSerializer(TestCase):
    def test_serializer(self):
        totals = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=150, percentage=150),
            resolved=ConversationsTotalsMetric(value=100, percentage=100),
            unresolved=ConversationsTotalsMetric(value=50, percentage=50),
            abandoned=ConversationsTotalsMetric(value=0, percentage=0),
            transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
        )
        serializer = ConversationTotalsMetricsSerializer(totals)
        data = serializer.data

        self.assertEqual(
            data["total_conversations"]["value"], totals.total_conversations.value
        )
        self.assertEqual(
            data["total_conversations"]["percentage"],
            totals.total_conversations.percentage,
        )
        self.assertEqual(data["resolved"]["value"], totals.resolved.value)
        self.assertEqual(data["resolved"]["percentage"], totals.resolved.percentage)
        self.assertEqual(data["unresolved"]["value"], totals.unresolved.value)
        self.assertEqual(data["unresolved"]["percentage"], totals.unresolved.percentage)


class TestConversationTotalsMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationTotalsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("project", serializer.validated_data)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(
            str(serializer.validated_data["start_date"]), "2021-01-01 00:00:00+00:00"
        )
        self.assertEqual(
            str(serializer.validated_data["end_date"]), "2021-01-02 23:59:59+00:00"
        )

    def test_serializer_invalid_start_date(self):
        serializer = ConversationTotalsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationTotalsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")
