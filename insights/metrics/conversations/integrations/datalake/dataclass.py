from dataclasses import dataclass


@dataclass(frozen=True)
class DatalakeConversationsTotalsMetrics:
    """
    Dataclass for conversations totals
    """

    value: int
    percentage: float
