from typing import TYPE_CHECKING
from insights.metrics.conversations.dataclass import RoomsByQueueMetric
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient


if TYPE_CHECKING:
    from uuid import UUID
    from datetime import datetime


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_rooms_numbers_by_queue(
        cls,
        project_uuid: "UUID",
        start_date: "datetime",
        end_date: "datetime",
        limit: int | None = None,
    ):
        """
        Get the rooms numbers by queue.
        """
        queues = list(
            ChatsClient().get_rooms_numbers_by_queue(project_uuid, start_date, end_date)
        )
        qty = len(queues)
        has_more = False

        if limit and qty > limit:
            queues = queues[:limit]
            has_more = True

        return RoomsByQueueMetric.from_values(queues, has_more=has_more)
