from dataclasses import dataclass

from insights.metrics.conversations.enums import ConversationsTimeseriesUnit


@dataclass(frozen=True)
class ConversationTotalsMetricsByType:
    """
    Dataclass to store conversation totals metrics by type
    """

    value: int
    percentage: float


@dataclass(frozen=True)
class ConversationTotalsMetrics:
    """
    Dataclass to store conversation totals metrics
    """

    total: int
    by_ai: ConversationTotalsMetricsByType
    by_human: ConversationTotalsMetricsByType

    @classmethod
    def from_values(cls, by_ai: int, by_human: int) -> "ConversationTotalsMetrics":
        """
        Create a ConversationTotalsMetrics instance from values
        """
        total = by_ai + by_human

        if total > 0:
            ai_percentage = (by_ai / total) * 100
            human_percentage = (by_human / total) * 100
        else:
            ai_percentage = 0.0
            human_percentage = 0.0

        return cls(
            total=total,
            by_ai=ConversationTotalsMetricsByType(
                value=by_ai, percentage=ai_percentage
            ),
            by_human=ConversationTotalsMetricsByType(
                value=by_human, percentage=human_percentage
            ),
        )


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
class SubjectItem:
    """
    A subject.
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class SubjectGroup:
    """
    A group of subjects.
    """

    name: str
    percentage: float
    subjects: list[SubjectItem]


@dataclass(frozen=True)
class SubjectsDistributionMetrics:
    """
    Metrics for the distribution of subjects in a conversation.
    """

    groups: list[SubjectGroup]


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
