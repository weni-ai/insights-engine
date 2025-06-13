from dataclasses import dataclass

from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue


@dataclass(frozen=True)
class QueueMetric:
    """
    Dataclass for the queue.
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class RoomsByQueueMetric:
    """
    Dataclass for the rooms by queue.
    """

    queues: list[QueueMetric]
    has_more: bool

    @classmethod
    def from_values(
        cls, queues: list[RoomsByQueue], has_more: bool
    ) -> "RoomsByQueueMetric":
        """
        Create a RoomsByQueueMetric instance from values
        """
        total_rooms = sum(queue.rooms_number for queue in queues)
        queues_metrics = []

        for queue in queues:
            queues_metrics.append(
                QueueMetric(
                    name=queue.queue_name,
                    percentage=round(queue.rooms_number / total_rooms * 100, 2),
                )
            )

        return cls(
            queues=queues_metrics,
            has_more=has_more,
        )
