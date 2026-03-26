from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VTEXOrdersBaseMetrics:
    """
    Dataclass to store VTEX orders metrics.
    """

    total_value: float = 0
    total_sell: int = 0
    max_value: float = float("-inf")
    min_value: float = float("inf")
    currency_code: str = ""
    last_authorized_date: Optional[str] = None
    processed_orders: set = field(default_factory=set)
