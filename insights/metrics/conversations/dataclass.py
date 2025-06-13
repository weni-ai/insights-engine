from dataclasses import dataclass


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
