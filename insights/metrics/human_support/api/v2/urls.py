from django.urls import path

from insights.metrics.human_support.api.v2.views import (
    AnalysisDetailedMonitoringStatusViewV2,
    AverageOrderValueViewV2,
    DetailedMonitoringAgentsViewV2,
    DetailedMonitoringStatusViewV2,
    SalesFunnelViewV2,
    TotalRevenueViewV2,
)

urlpatterns = [
    path(
        "detailed-monitoring/agents/",
        DetailedMonitoringAgentsViewV2.as_view(),
    ),
    path(
        "detailed-monitoring/status/",
        DetailedMonitoringStatusViewV2.as_view(),
    ),
    path(
        "analysis/detailed-monitoring/status/",
        AnalysisDetailedMonitoringStatusViewV2.as_view(),
    ),
    path(
        "sales/total-revenue/",
        TotalRevenueViewV2.as_view(),
    ),
    path(
        "sales/average-order-value/",
        AverageOrderValueViewV2.as_view(),
    ),
    path(
        "sales/sales-funnel/",
        SalesFunnelViewV2.as_view(),
    ),
]
