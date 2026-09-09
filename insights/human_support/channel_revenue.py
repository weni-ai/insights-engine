from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ChannelRevenueSaleRow:
    channel: str
    value: float = 0.0


@dataclass
class ChannelRevenueSaleData:
    metric: str = "sale"
    currency_code: str = ""
    rows: list[ChannelRevenueSaleRow] = field(default_factory=list)


class ChannelRevenueSaleSource(Protocol):
    """
    Provides revenue or sales volume of human support rooms by channel.
    """

    def get_channel_revenue_sale(self, params: dict) -> ChannelRevenueSaleData:
        raise NotImplementedError


class NullChannelRevenueSaleSource:
    """
    Used while assisted sales data has no origin to be read from.
    """

    def get_channel_revenue_sale(self, params: dict) -> ChannelRevenueSaleData:
        metric = params.get("metric") or "sale"
        if metric not in ("revenue", "sale"):
            metric = "sale"
        return ChannelRevenueSaleData(metric=metric)


def calculate_share_percentage(total: float, value: float) -> float:
    if not total:
        return 0.0

    return round((value / total) * 100, 2)
