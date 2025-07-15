from dataclasses import dataclass


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
