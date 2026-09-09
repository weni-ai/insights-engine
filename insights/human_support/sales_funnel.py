from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SalesFunnelData:
    leads_count: int = 0
    purchases_count: int = 0


class SalesFunnelSource(Protocol):
    """
    Provides the sales funnel of human support rooms in a period.
    """

    def get_sales_funnel(self, params: dict) -> SalesFunnelData:
        raise NotImplementedError


class NullSalesFunnelSource:
    """
    Used while assisted sales data has no origin to be read from.
    """

    def get_sales_funnel(self, params: dict) -> SalesFunnelData:
        return SalesFunnelData()


def calculate_conversion_percentage(leads_count: int, purchases_count: int) -> float:
    if not leads_count:
        return 0.0

    return round((purchases_count / leads_count) * 100, 2)
