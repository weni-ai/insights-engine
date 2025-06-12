from django.test import TestCase

from insights.metrics.conversations.dataclass import SubjectMetricData, SubjectsMetrics
from insights.metrics.conversations.enums import ConversationsSubjectsType
from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    SubjectsMetricsSerializer,
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
