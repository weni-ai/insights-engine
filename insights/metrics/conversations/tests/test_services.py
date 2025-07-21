from datetime import datetime
from uuid import UUID
from django.test import TestCase
from django.core.cache import cache

from insights.metrics.conversations.dataclass import TopicsDistributionMetrics
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project
from insights.sources.integrations.tests.mock_clients import MockNexusClient


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService(
        datalake_service=MockConversationsMetricsService(),
        nexus_client=MockNexusClient(),
    )

    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

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

    def test_get_topics(self):
        topics = self.service.get_topics(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9")
        )

        self.assertEqual(len(topics), 1)

    def test_get_subtopics(self):
        subtopics = self.service.get_subtopics(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )

        self.assertEqual(len(subtopics), 1)

    def test_create_topic(self):
        self.service.create_topic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            name="Cancelamento",
            description="Quando cliente pede para cancelar um pedido",
        )

    def test_create_subtopic(self):
        self.service.create_subtopic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            name="Cancelamento",
            description="Quando cliente pede para cancelar um pedido",
        )

    def test_delete_topic(self):
        self.service.delete_topic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )

    def test_delete_subtopic(self):
        self.service.delete_subtopic(
            project_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            topic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
            subtopic_uuid=UUID("2026cedc-67f6-4a04-977a-55cc581defa9"),
        )
