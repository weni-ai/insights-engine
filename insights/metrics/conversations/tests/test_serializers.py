import uuid

from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    ConversationsTimeseriesData,
    ConversationsTimeseriesMetrics,
    SubjectMetricData,
    SubjectsMetrics,
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
)
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
    NPSQueryParamsSerializer,
    NPSSerializer,
    RoomsByQueueMetricQueryParamsSerializer,
    SubjectsMetricsSerializer,
    SubtopicSerializer,
    TopicSerializer,
    TopicsDistributionMetricsQueryParamsSerializer,
    TopicsDistributionMetricsSerializer,
)
from insights.projects.models import Project


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


class TestConversationTotalsMetricsSerializer(TestCase):
    def test_serializer(self):
        totals = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=150, percentage=150),
            resolved=ConversationsTotalsMetric(value=100, percentage=100),
            unresolved=ConversationsTotalsMetric(value=50, percentage=50),
            abandoned=ConversationsTotalsMetric(value=0, percentage=0),
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
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

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


class TestConversationsTimeseriesDataSerializer(TestCase):
    def test_validate_data_for_day_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.DAY,
            total=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-01-02", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-01-02", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-01-02", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-01-02", "value": 200},
            ],
        )

    def test_validate_data_for_hour_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.HOUR,
            total=[
                ConversationsTimeseriesData(label="10h", value=100),
                ConversationsTimeseriesData(label="11h", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="10h", value=100),
                ConversationsTimeseriesData(label="11h", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "10h", "value": 100},
                {"label": "11h", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "10h", "value": 100},
                {"label": "11h", "value": 200},
            ],
        )

    def test_validate_data_for_month_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.MONTH,
            total=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-02-01", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-02-01", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-02-01", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-02-01", "value": 200},
            ],
        )


class TestConversationsTimeseriesMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["unit"], ConversationsTimeseriesUnit.DAY
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

    def test_serializer_invalid_start_date(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")

    def test_serializer_invalid_unit(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "unit": "CENTURY",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("unit", serializer.errors)
        self.assertEqual(serializer.errors["unit"][0].code, "invalid_choice")


class TestSubjectMetricDataSerializer(TestCase):
    def test_serializer(self):
        subject_1 = SubjectMetricData(
            name="Test Subject 1",
            percentage=0.5,
        )
        subject_2 = SubjectMetricData(
            name="Test Subject 2",
            percentage=0.5,
        )

        metrics = SubjectsMetrics(
            has_more=False,
            subjects=[subject_1, subject_2],
        )

        serializer = SubjectsMetricsSerializer(metrics)
        data = serializer.data

        self.assertEqual(data["has_more"], metrics.has_more)
        self.assertEqual(
            data["subjects"][0],
            {"name": subject_1.name, "percentage": subject_1.percentage},
        )
        self.assertEqual(
            data["subjects"][1],
            {"name": subject_2.name, "percentage": subject_2.percentage},
        )

    def test_serializer_without_subjects(self):
        metrics = SubjectsMetrics(
            has_more=True,
            subjects=[],
        )

        serializer = SubjectsMetricsSerializer(metrics)
        data = serializer.data

        self.assertEqual(data["has_more"], metrics.has_more)
        self.assertEqual(data["subjects"], [])


class TestConversationsSubjectsMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationsSubjectsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "type": ConversationsSubjectsType.GENERAL,
                "limit": 10,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(
            serializer.validated_data["type"], ConversationsSubjectsType.GENERAL
        )

    def test_serializer_invalid_start_date(self):
        serializer = ConversationsSubjectsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationsSubjectsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")

    def test_serializer_invalid_type(self):
        serializer = ConversationsSubjectsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "type": "invalid",
                "limit": 10,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")

    def test_serializer_invalid_limit(self):
        serializer = ConversationsSubjectsMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "type": ConversationsSubjectsType.GENERAL,
                "limit": "invalid",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("limit", serializer.errors)
        self.assertEqual(serializer.errors["limit"][0].code, "invalid")


class TestRoomsByQueueMetricQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = RoomsByQueueMetricQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )

    def test_serializer_invalid_start_date(self):
        serializer = RoomsByQueueMetricQueryParamsSerializer(
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
        serializer = RoomsByQueueMetricQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestNPSQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = NPSQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "type": NPSType.AI,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("project", serializer.validated_data)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(serializer.validated_data["type"], NPSType.AI)

    def test_serializer_invalid_project_uuid(self):
        serializer = NPSQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "type": NPSType.HUMAN,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")

    def test_serializer_invalid_start_date(self):
        serializer = NPSQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
                "type": NPSType.HUMAN,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )


class TestNPSSerializer(TestCase):
    def test_serializer(self):
        serializer = NPSSerializer(
            data={
                "score": 5,
                "total_responses": 10,
                "promoters": 5,
                "detractors": 3,
                "passives": 2,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["score"], 5)
        self.assertEqual(serializer.validated_data["total_responses"], 10)
        self.assertEqual(serializer.validated_data["promoters"], 5)
        self.assertEqual(serializer.validated_data["detractors"], 3)
        self.assertEqual(serializer.validated_data["passives"], 2)


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
        subtopic = SubtopicMetrics(
            uuid=uuid.uuid4(),
            name="Test Subtopic",
            percentage=0.5,
        )
        serializer = SubtopicSerializer(subtopic)
        self.assertEqual(serializer.data["name"], "Test Subtopic")
        self.assertEqual(serializer.data["percentage"], 0.5)


class TestTopicSerializer(TestCase):
    def test_serializer(self):
        topic = TopicMetrics(
            uuid=uuid.uuid4(),
            name="Test Topic",
            percentage=0.5,
            subtopics=[
                SubtopicMetrics(
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
            TopicMetrics(
                uuid=uuid.uuid4(),
                name="Test Topic",
                percentage=0.5,
                subtopics=[
                    SubtopicMetrics(
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
