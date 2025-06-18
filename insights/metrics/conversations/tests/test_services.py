from datetime import datetime
from django.test import TestCase

from insights.metrics.conversations.dataclass import SubjectsDistributionMetrics
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def test_get_subjects_distribution(self):
        project = Project.objects.create(
            name="Test Project",
        )
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 2)
        subjects_distribution = self.service.get_subjects_distribution(
            project, start_date, end_date
        )

        self.assertIsInstance(subjects_distribution, SubjectsDistributionMetrics)

        self.assertEqual(subjects_distribution.groups[0].name, "Status de solicitação")
        self.assertEqual(subjects_distribution.groups[0].percentage, 60)
        self.assertEqual(
            subjects_distribution.groups[0].subjects[0].name, "Troca de produto"
        )
        self.assertEqual(subjects_distribution.groups[0].subjects[0].percentage, 60)
        self.assertEqual(
            subjects_distribution.groups[0].subjects[1].name, "Pedido não localizado"
        )
        self.assertEqual(subjects_distribution.groups[0].subjects[1].percentage, 15)
        self.assertEqual(
            subjects_distribution.groups[0].subjects[2].name, "Status do pedido"
        )
        self.assertEqual(subjects_distribution.groups[0].subjects[2].percentage, 13)
