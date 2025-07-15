from uuid import UUID
from django.test import TestCase

from insights.metrics.conversations.services import ConversationsMetricsService
from insights.sources.integrations.tests.mock_clients import MockNexusClient


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService(nexus_client=MockNexusClient())

    def test_get_topics(self):
        topics = self.service.get_topics(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        )

        self.assertEqual(len(topics), 1)
