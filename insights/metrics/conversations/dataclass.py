from dataclasses import dataclass


@dataclass(frozen=True)
class SubtopicMetrics:
    """
    A subtopic.
    """

    uuid: str
    name: str
    percentage: float


@dataclass(frozen=True)
class TopicMetrics:
    """
    A topics, that consists of subtopics.
    """

    uuid: str | None
    name: str
    percentage: float
    subtopics: list[SubtopicMetrics]


@dataclass(frozen=True)
class TopicsDistributionMetrics:
    """
    Metrics for the distribution of topics in a conversation.
    """

    topics: list[TopicMetrics]
