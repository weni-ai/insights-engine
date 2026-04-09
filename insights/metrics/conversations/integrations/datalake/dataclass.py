from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResultMetric:
    """
    Dataclass to store tool result metric data.
    """

    agent_uuid: Optional[str] = None
    count: int = 0


@dataclass(frozen=True)
class SalesFunnelData:
    """
    Dataclass to store sales funnel data.
    """

    currency_code: str = ""
    leads_count: int = 0
    total_orders_count: int = 0
    total_orders_value: int = 0


@dataclass
class AgentInvocationMetric:
    """
    Dataclass to store agent invocation metric data.
    """

    agent_uuid: Optional[str] = None
    count: int = 0


@dataclass(frozen=True)
class CrosstabSource:
    """
    Dataclass to store crosstab source data.
    """

    key: str  # Event key
    field: str = "value"  # Event field name to be used to retrieve the value
