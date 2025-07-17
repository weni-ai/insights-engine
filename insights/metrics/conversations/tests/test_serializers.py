from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    SubjectGroup,
    SubjectItem,
    SubjectsDistributionMetrics,
)
from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    SubjectItemSerializer,
    TopicsDistributionMetricsQueryParamsSerializer,
    SubjectGroupSerializer,
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
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestSubjectItemSerializer(TestCase):
    def test_serializer(self):
        subject = SubjectItem(name="Test Subject", percentage=0.5)
        serializer = SubjectItemSerializer(subject)
        self.assertEqual(serializer.data["name"], "Test Subject")
        self.assertEqual(serializer.data["percentage"], 0.5)


class TestSubjectGroupSerializer(TestCase):
    def test_serializer(self):
        group = SubjectGroup(
            name="Test Group",
            percentage=0.5,
            subjects=[SubjectItem(name="Test Subject", percentage=0.5)],
        )
        serializer = SubjectGroupSerializer(group)
        self.assertEqual(serializer.data["name"], "Test Group")
        self.assertEqual(serializer.data["percentage"], 0.5)
        self.assertEqual(
            serializer.data["subjects"],
            [{"name": "Test Subject", "percentage": 0.5}],
        )


class TestTopicsDistributionMetricsSerializer(TestCase):
    def test_serializer(self):
        groups = [
            SubjectGroup(
                name="Test Group",
                percentage=0.5,
                subjects=[SubjectItem(name="Test Subject", percentage=0.5)],
            )
        ]
        subjects_distribution_metrics = SubjectsDistributionMetrics(groups=groups)
        serializer = TopicsDistributionMetricsSerializer(subjects_distribution_metrics)
        for group_data, group in zip(serializer.data["groups"], groups):
            self.assertEqual(group_data["name"], group.name)
            self.assertEqual(group_data["percentage"], group.percentage)
            for subject_data, subject in zip(group_data["subjects"], group.subjects):
                self.assertEqual(subject_data["name"], subject.name)
                self.assertEqual(subject_data["percentage"], subject.percentage)
