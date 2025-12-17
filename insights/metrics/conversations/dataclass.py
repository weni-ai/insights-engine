from dataclasses import dataclass


from insights.metrics.conversations.enums import AvailableWidgets


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
    transferred_to_human: ConversationsTotalsMetric


@dataclass(frozen=True)
class NPSMetrics:
    total_responses: int
    promoters: float
    passives: float
    detractors: float
    score: float


@dataclass(frozen=True)
class SalesFunnelMetrics:
    """
    Dataclass for sales funnel metrics
    """

    leads_count: int
    total_orders_count: int
    total_orders_value: int  # In cents
    currency_code: str

    @property
    def average_ticket(self) -> int:
        """
        Get the average ticket
        """
        return round(
            self.total_orders_value / self.total_orders_count
            if self.total_orders_count > 0
            else 0
        )


@dataclass(frozen=True)
class AvailableWidgetsList:
    """
    List of available widgets
    """

    available_widgets: list[AvailableWidgets]


@dataclass(frozen=True)
class CrosstabSubItemData:
    """
    Dataclass for crosstab sub item data
    """

    title: str
    count: int
    percentage: float


@dataclass(frozen=True)
class CrosstabItemData:
    """
    Dataclass for crosstab item data
    """

    title: str
    total: int  # sum of all related events
    subitems: list[CrosstabSubItemData]
