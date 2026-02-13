from typing import TypedDict


class PricingDataPoint(TypedDict):
    """
    TypedDict for pricing data point
    """

    start: int
    end: int
    pricing_category: str
    volume: int
    cost: int
