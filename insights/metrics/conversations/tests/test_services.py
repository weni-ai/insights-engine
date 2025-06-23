import datetime
from django.test import TestCase

from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.tests.mock import NPS_METRICS_MOCK_DATA
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self) -> None:
        self.project = Project.objects.create(name="Test Project")

    def test_get_nps(self):
        """
        Test the NPS method
        """
        nps = self.service.get_nps(
            self.project, datetime.date(2025, 1, 1), datetime.date(2025, 1, 31)
        )

        self.assertEqual(nps.score, NPS_METRICS_MOCK_DATA["score"])
        self.assertEqual(nps.total_responses, NPS_METRICS_MOCK_DATA["total_responses"])
        self.assertEqual(nps.promoters, NPS_METRICS_MOCK_DATA["promoters"])
        self.assertEqual(nps.detractors, NPS_METRICS_MOCK_DATA["detractors"])
        self.assertEqual(nps.passives, NPS_METRICS_MOCK_DATA["passives"])
