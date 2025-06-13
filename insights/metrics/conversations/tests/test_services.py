from datetime import datetime, timedelta
from django.test import TestCase

from insights.metrics.conversations.dataclass import SubjectMetricData, SubjectsMetrics
from insights.metrics.conversations.enums import ConversationsSubjectsType
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
)
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self) -> None:
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()

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
