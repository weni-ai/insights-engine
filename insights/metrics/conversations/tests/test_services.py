from datetime import datetime, timedelta
from django.test import TestCase

from insights.metrics.conversations.dataclass import ConversationTotalsMetrics
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
)
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()

    def test_get_totals(self):
        totals = self.service.get_totals(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(totals, ConversationTotalsMetrics)
        self.assertEqual(
            totals.total,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
            + CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )
        self.assertEqual(
            totals.by_ai.value, CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
        )
        self.assertEqual(
            totals.by_ai.percentage,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"] / totals.total * 100,
        )
        self.assertEqual(
            totals.by_human.value, CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"]
        )
        self.assertEqual(
            totals.by_human.percentage,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"] / totals.total * 100,
        )
