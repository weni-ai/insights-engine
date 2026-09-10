from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RepresentativePerformanceRow:
    representative: str
    conversations: int = 0
    sales: int = 0
    revenue: float = 0.0


@dataclass
class RepresentativePerformanceData:
    currency_code: str = ""
    rows: list[RepresentativePerformanceRow] = field(default_factory=list)


class RepresentativePerformanceSource(Protocol):
    """
    Provides assisted-sales performance of human support rooms by representative.
    """

    def get_performance_by_representative(
        self, params: dict
    ) -> RepresentativePerformanceData:
        raise NotImplementedError


class NullRepresentativePerformanceSource:
    """
    Used while assisted sales data has no origin to be read from.
    """

    def get_performance_by_representative(
        self, params: dict
    ) -> RepresentativePerformanceData:
        return RepresentativePerformanceData()


def calculate_average_order_value(revenue: float, sales: int) -> float:
    if not sales:
        return 0.0

    return float(round(revenue / sales))
