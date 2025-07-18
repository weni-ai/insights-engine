from datetime import datetime
from django.test import TestCase

from insights.metrics.conversations.dataclass import TopicsDistributionMetrics
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService(
        datalake_service=MockConversationsMetricsService()
    )

    def test_get_topics_distribution(self):
        project = Project.objects.create(
            name="Test Project",
        )
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 2)
        topics_distribution = self.service.get_topics_distribution(
            project, start_date, end_date, ConversationType.AI
        )

        self.assertIsInstance(topics_distribution, TopicsDistributionMetrics)
