from dataclasses import dataclass


@dataclass(frozen=True)
class DatalakeConversationsTotalsMetric:
    """
    Dataclass for conversations totals
    """

    value: int
    percentage: float


@dataclass(frozen=True)
class DatalakeConversationsTotalsMetrics:
    """
    Dataclass for conversations totals metrics
    """

    total_conversations: DatalakeConversationsTotalsMetric
    resolved: DatalakeConversationsTotalsMetric
    unresolved: DatalakeConversationsTotalsMetric
