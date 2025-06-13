from unittest.mock import patch
import uuid
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.dataclass import RoomsByQueueMetric
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.metrics.conversations.services import ConversationsMetricsService


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

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
            project_uuid=uuid.uuid4(),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now(),
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric.from_values(rooms_by_queue, has_more=False),
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
            project_uuid=uuid.uuid4(),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now(),
            limit=1,
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric.from_values(rooms_by_queue[:1], has_more=True),
        )
