from datetime import datetime
from django.test import TestCase

from insights.metrics.conversations.dataclass import TopicsDistributionMetrics
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def test_get_topics_distribution(self):
        project = Project.objects.create(
            name="Test Project",
        )
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2021, 1, 2)
        topics_distribution = self.service.get_topics_distribution(
            project, start_date, end_date
        )

        self.assertIsInstance(topics_distribution, TopicsDistributionMetrics)
