import uuid

from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    Subtopic,
    Topic,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType
from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    SubtopicSerializer,
    TopicSerializer,
    TopicsDistributionMetricsQueryParamsSerializer,
    TopicsDistributionMetricsSerializer,
)


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
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

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
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

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
        subtopic = Subtopic(
            uuid=uuid.uuid4(),
            name="Test Subtopic",
            percentage=0.5,
        )
        serializer = SubtopicSerializer(subtopic)
        self.assertEqual(serializer.data["name"], "Test Subtopic")
        self.assertEqual(serializer.data["percentage"], 0.5)


class TestTopicSerializer(TestCase):
    def test_serializer(self):
        topic = Topic(
            uuid=uuid.uuid4(),
            name="Test Topic",
            percentage=0.5,
            subtopics=[
                Subtopic(
                    uuid=uuid.uuid4(),
                    name="Test Subtopic",
                    percentage=0.5,
                )
            ],
        )
        serializer = TopicSerializer(topic)
        self.assertEqual(serializer.data["uuid"], str(topic.uuid))
        self.assertEqual(serializer.data["name"], "Test Topic")
        self.assertEqual(serializer.data["percentage"], 0.5)
        self.assertEqual(
            [
                {
                    "uuid": str(subtopic.uuid),
                    "name": subtopic.name,
                    "percentage": subtopic.percentage,
                }
                for subtopic in topic.subtopics
            ],
            serializer.data["subtopics"],
        )


class TestTopicsDistributionMetricsSerializer(TestCase):
    def test_serializer(self):
        topics = [
            Topic(
                uuid=uuid.uuid4(),
                name="Test Topic",
                percentage=0.5,
                subtopics=[
                    Subtopic(
                        uuid=uuid.uuid4(),
                        name="Test Subtopic",
                        percentage=0.5,
                    )
                ],
            )
        ]
        topics_distribution_metrics = TopicsDistributionMetrics(topics=topics)
        serializer = TopicsDistributionMetricsSerializer(topics_distribution_metrics)
        for topic_data, topic in zip(serializer.data["topics"], topics):
            self.assertEqual(topic_data["uuid"], str(topic.uuid))
            self.assertEqual(topic_data["name"], topic.name)
            self.assertEqual(topic_data["percentage"], topic.percentage)
            for subtopic_data, subtopic in zip(
                topic_data["subtopics"], topic.subtopics
            ):
                self.assertEqual(subtopic_data["uuid"], str(subtopic.uuid))
                self.assertEqual(subtopic_data["name"], subtopic.name)
                self.assertEqual(subtopic_data["percentage"], subtopic.percentage)
