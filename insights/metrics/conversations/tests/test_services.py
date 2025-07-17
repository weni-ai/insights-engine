from datetime import datetime, timedelta
from django.test import TestCase

from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService(
        datalake_service=MockConversationsMetricsService()
    )

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

        self.assertIsInstance(totals, ConversationsTotalsMetrics)
