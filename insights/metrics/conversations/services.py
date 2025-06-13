from typing import TYPE_CHECKING
from insights.metrics.conversations.dataclass import QueueMetric, RoomsByQueueMetric
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

        queues_metrics = []
        total_rooms = sum(queue.rooms_number for queue in queues)

        queues_range = min(qty, limit) if limit else qty

        for queue in queues[:queues_range]:
            queues_metrics.append(
                QueueMetric(
                    name=queue.queue_name,
                    percentage=round(queue.rooms_number / total_rooms * 100, 2),
                )
            )

        if limit and qty > limit:
            has_more = True

        return RoomsByQueueMetric(queues=queues_metrics, has_more=has_more)
