from typing import TYPE_CHECKING
from datetime import datetime

import pytz
from insights.metrics.conversations.dataclass import QueueMetric, RoomsByQueueMetric
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient


if TYPE_CHECKING:
    from uuid import UUID
    from datetime import date
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_rooms_numbers_by_queue(
        cls,
        project: "Project",
        start_date: "date",
        end_date: "date",
        limit: int | None = None,
    ):
        """
        Get the rooms numbers by queue.
        """

        if project.timezone is None:
            tz = pytz.utc
        else:
            tz = pytz.timezone(project.timezone)

        # Create naive datetime at midnight in the project's timezone
        local_start = datetime.combine(start_date, datetime.min.time())
        local_end = datetime.combine(end_date, datetime.max.time())

        # Convert to UTC while preserving the intended local time
        start_datetime = tz.localize(local_start).astimezone(pytz.UTC)
        end_datetime = tz.localize(local_end).astimezone(pytz.UTC)

        queues = list(
            ChatsClient().get_rooms_numbers_by_queue(
                project.uuid,
                start_datetime,
                end_datetime,
            )
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
