from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RoomsByQueue:
    """
    Dataclass for the rooms by queue.
    """

    queue_uuid: UUID
    queue_name: str
    rooms_number: int
