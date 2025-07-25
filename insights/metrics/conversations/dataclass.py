from dataclasses import dataclass

from insights.metrics.conversations.enums import ConversationsTimeseriesUnit


@dataclass(frozen=True)
class ConversationsTotalsMetric:
    """
    Dataclass for conversations totals
    """

    value: int
    percentage: float


@dataclass(frozen=True)
class ConversationsTotalsMetrics:
    """
    Dataclass for conversations totals metrics
    """

    total_conversations: ConversationsTotalsMetric
    resolved: ConversationsTotalsMetric
    unresolved: ConversationsTotalsMetric
    abandoned: ConversationsTotalsMetric
    transferred_to_human: bool


@dataclass(frozen=True)
class ConversationsTimeseriesData:
    """
    Data class to store the data for the conversations timeseries metrics.
    """

    label: str
    value: int


@dataclass(frozen=True)
class ConversationsTimeseriesMetrics:
    """
    Data class to store the conversations timeseries metrics.
    """

    unit: ConversationsTimeseriesUnit
    total: list[ConversationsTimeseriesData]
    by_human: list[ConversationsTimeseriesData]


@dataclass(frozen=True)
class SubjectMetricData:
    """
    Dataclass for subjects metrics by type
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class SubjectsMetrics:
    """
    Dataclass for subjects metrics
    """

    has_more: bool
    subjects: list[SubjectMetricData]


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


@dataclass
class NPS:
    """
    NPS is a metric that measures the Net Promoter Score of a product or service.
    """

    score: float
    total_responses: int
    promoters: int
    detractors: int
    passives: int


@dataclass(frozen=True)
class SubtopicTopicRelation:
    """
    Subtopic -> Topic relation
    """

    subtopic_uuid: str
    subtopic_name: str
    topic_uuid: str
    topic_name: str
