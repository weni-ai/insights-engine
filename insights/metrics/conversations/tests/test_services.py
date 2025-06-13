from unittest.mock import patch
import uuid
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.dataclass import RoomsByQueueMetric, QueueMetric
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project=self.project,
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date(),
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                    QueueMetric(name="Test Queue 2", percentage=66.67),
                ],
                has_more=False,
            ),
        )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue_with_limit(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project=self.project,
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date(),
            limit=1,
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                ],
                has_more=True,
            ),
        )
