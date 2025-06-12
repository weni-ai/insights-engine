from dataclasses import dataclass

from insights.metrics.conversations.enums import ConversationsTimeseriesUnit


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
