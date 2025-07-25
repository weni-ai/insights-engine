from datetime import datetime, timedelta
from uuid import UUID

from insights.projects.models import Project
from django.test import TestCase
from django.core.cache import cache

from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.integrations.datalake.tests.mock_services import (
    MockConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.sources.integrations.tests.mock_clients import MockNexusClient


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService(
        nexus_client=MockNexusClient(),
        datalake_service=MockConversationsMetricsService(),
    )

    def setUp(self) -> None:
        self.project = Project.objects.create(name="Test Project")
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

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

    def test_get_totals(self):
        totals = self.service.get_totals(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertIsInstance(totals, ConversationsTotalsMetrics)
