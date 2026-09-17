from __future__ import annotations

from insights.human_support.average_order_value import AverageOrderValueData
from insights.human_support.channel_revenue import (
    ChannelRevenueSaleData,
    ChannelRevenueSaleRow,
)
from insights.human_support.performance import (
    RepresentativePerformanceData,
    RepresentativePerformanceRow,
)
from insights.human_support.revenue import RevenueData
from insights.human_support.sales_funnel import SalesFunnelData
from insights.sources.channels.enums import Channel


CURRENT_REVENUE = RevenueData(total=428450.0, currency_code="USD")
PREVIOUS_REVENUE = RevenueData(total=362480.0, currency_code="USD")

CURRENT_AVERAGE_ORDER_VALUE = AverageOrderValueData(value=284.0, currency_code="USD")
PREVIOUS_AVERAGE_ORDER_VALUE = AverageOrderValueData(value=240.0, currency_code="USD")

SALES_FUNNEL = SalesFunnelData(leads_count=45000, purchases_count=4250)

CHANNEL_SALE_ROWS = [
    ChannelRevenueSaleRow(channel=Channel.WHATSAPP, value=620),
    ChannelRevenueSaleRow(channel=Channel.TEAMS, value=510),
    ChannelRevenueSaleRow(channel=Channel.EMAIL, value=460),
    ChannelRevenueSaleRow(channel=Channel.INSTAGRAM, value=390),
    ChannelRevenueSaleRow(channel=Channel.FACEBOOK, value=330),
    ChannelRevenueSaleRow(channel=Channel.OTHERS, value=330),
    ChannelRevenueSaleRow(channel=Channel.SHOPPING_ASSISTANT, value=210),
]

CHANNEL_REVENUE_ROWS = [
    ChannelRevenueSaleRow(channel=Channel.WHATSAPP, value=176800.0),
    ChannelRevenueSaleRow(channel=Channel.TEAMS, value=84210.0),
    ChannelRevenueSaleRow(channel=Channel.EMAIL, value=51840.0),
    ChannelRevenueSaleRow(channel=Channel.INSTAGRAM, value=46120.0),
    ChannelRevenueSaleRow(channel=Channel.FACEBOOK, value=33150.0),
    ChannelRevenueSaleRow(channel=Channel.OTHERS, value=22100.0),
    ChannelRevenueSaleRow(channel=Channel.SHOPPING_ASSISTANT, value=14230.0),
]

REPRESENTATIVE_EMAILS = {
    "Emma Wilson": "emma@example.com",
    "Lucas Moreira": "lucas@example.com",
    "Sofia Almeida": "sofia@example.com",
    "Daniel Okafor": "daniel@example.com",
}

CURRENT_PERFORMANCE_ROWS = [
    RepresentativePerformanceRow(
        representative="Emma Wilson",
        conversations=612,
        sales=254,
        revenue=72340,
    ),
    RepresentativePerformanceRow(
        representative="Lucas Moreira",
        conversations=574,
        sales=218,
        revenue=64120,
    ),
    RepresentativePerformanceRow(
        representative="Sofia Almeida",
        conversations=498,
        sales=176,
        revenue=58910,
    ),
    RepresentativePerformanceRow(
        representative="Daniel Okafor",
        conversations=531,
        sales=168,
        revenue=51470,
    ),
]

PREVIOUS_PERFORMANCE_ROWS = [
    RepresentativePerformanceRow(representative="Emma Wilson", revenue=64359.43),
    RepresentativePerformanceRow(representative="Lucas Moreira", revenue=59315.45),
    RepresentativePerformanceRow(representative="Sofia Almeida", revenue=56319.31),
    RepresentativePerformanceRow(representative="Daniel Okafor", revenue=52681.68),
]


class MockRevenueSource:
    def __init__(self) -> None:
        self._calls = 0

    def get_revenue(self, params: dict) -> RevenueData:
        self._calls += 1
        if self._calls == 1:
            return CURRENT_REVENUE
        return PREVIOUS_REVENUE


class MockAverageOrderValueSource:
    def __init__(self) -> None:
        self._calls = 0

    def get_average_order_value(self, params: dict) -> AverageOrderValueData:
        self._calls += 1
        if self._calls == 1:
            return CURRENT_AVERAGE_ORDER_VALUE
        return PREVIOUS_AVERAGE_ORDER_VALUE


class MockSalesFunnelSource:
    def get_sales_funnel(self, params: dict) -> SalesFunnelData:
        return SALES_FUNNEL


class MockChannelRevenueSaleSource:
    def get_channel_revenue_sale(self, params: dict) -> ChannelRevenueSaleData:
        metric = params.get("metric") or "sale"
        if metric not in ("revenue", "sale"):
            metric = "sale"

        rows = CHANNEL_REVENUE_ROWS if metric == "revenue" else CHANNEL_SALE_ROWS
        channels = params.get("channels")
        if channels:
            allowed = set(channels)
            rows = [row for row in rows if row.channel in allowed]

        return ChannelRevenueSaleData(
            metric=metric,
            currency_code="USD" if metric == "revenue" else "",
            rows=list(rows),
        )


class MockRepresentativePerformanceSource:
    def __init__(self) -> None:
        self._calls = 0

    def get_performance_by_representative(
        self, params: dict
    ) -> RepresentativePerformanceData:
        self._calls += 1
        rows = (
            CURRENT_PERFORMANCE_ROWS if self._calls == 1 else PREVIOUS_PERFORMANCE_ROWS
        )
        agent = params.get("agent")
        if agent:
            rows = [
                row
                for row in rows
                if row.representative == agent
                or REPRESENTATIVE_EMAILS.get(row.representative) == agent
            ]

        return RepresentativePerformanceData(currency_code="USD", rows=list(rows))
