from dataclasses import dataclass


@dataclass(frozen=True)
class SalesFunnelData:
    """
    Dataclass to store sales funnel data.
    """

    currency_code: str = ""
    leads_count: int = 0
    total_orders_count: int = 0
    total_orders_value: int = 0


@dataclass(frozen=True)
class CrosstabSource:
    """
    Dataclass to store crosstab source data.
    """

    key: str  # Event key
    field: str = "value"  # Event field name to be used to retrieve the value
