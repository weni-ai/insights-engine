from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Subtopic:
    """
    A subtopic.
    """

    uuid: UUID
    name: str
    percentage: float


@dataclass(frozen=True)
class Topic:
    """
    A topics, that consists of subtopics.
    """

    uuid: UUID
    name: str
    percentage: float
    subtopics: list[Subtopic]


@dataclass(frozen=True)
class TopicsDistributionMetrics:
    """
    Metrics for the distribution of topics in a conversation.
    """

    topics: list[Topic]
