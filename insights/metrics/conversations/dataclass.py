from dataclasses import dataclass


@dataclass(frozen=True)
class SubtopicMetrics:
    """
    A subtopic.
    """

    uuid: str | None
    name: str
    quantity: int
    percentage: float


@dataclass(frozen=True)
class ConversationsTotalsMetric:
    """
    Dataclass for conversations totals
    """

    value: int
    percentage: float


@dataclass(frozen=True)
class TopicMetrics:
    """
    A topics, that consists of subtopics.
    """

    uuid: str | None
    name: str
    quantity: int
    percentage: float
    subtopics: list[SubtopicMetrics]


@dataclass(frozen=True)
class TopicsDistributionMetrics:
    """
    Metrics for the distribution of topics in a conversation.
    """

    topics: list[TopicMetrics]


@dataclass(frozen=True)
class SubtopicTopicRelation:
    """
    Subtopic -> Topic relation
    """

    subtopic_uuid: str
    subtopic_name: str
    topic_uuid: str
    topic_name: str


@dataclass(frozen=True)
class ConversationsTotalsMetrics:
    """
    Dataclass for conversations totals metrics
    """

    total_conversations: ConversationsTotalsMetric
    resolved: ConversationsTotalsMetric
    unresolved: ConversationsTotalsMetric
    abandoned: ConversationsTotalsMetric
    transferred_to_human: ConversationsTotalsMetric


@dataclass(frozen=True)
class NPSMetrics:
    total_responses: int
    promoters: int
    passives: int
    detractors: int
    score: int
