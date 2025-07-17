from dataclasses import dataclass


@dataclass(frozen=True)
class Subtopic:
    """
    A subtopic.
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class Topic:
    """
    A topics, that consists of subtopics.
    """

    name: str
    percentage: float
    topics: list[Subtopic]


@dataclass(frozen=True)
class TopicsDistributionMetrics:
    """
    Metrics for the distribution of topics in a conversation.
    """

    topics: list[Topic]
