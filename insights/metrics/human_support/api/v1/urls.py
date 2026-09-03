from django.urls import path

from insights.metrics.human_support.api.v1.views import (
    DetailedMonitoringOnGoingView,
    DetailedMonitoringAwaitingView,
    DetailedMonitoringAgentsView,
    DetailedMonitoringAgentsTotalsView,
    DetailedMonitoringStatusView,
    AnalysisDetailedMonitoringStatusView,
    TotalRevenueView,
)

urlpatterns = [
    path(
        "detailed-monitoring/on-going/",
        DetailedMonitoringOnGoingView.as_view(),
    ),
    path(
        "detailed-monitoring/awaiting/",
        DetailedMonitoringAwaitingView.as_view(),
    ),
    path(
        "detailed-monitoring/agents/",
        DetailedMonitoringAgentsView.as_view(),
    ),
    path(
        "detailed-monitoring/agents_totals/",
        DetailedMonitoringAgentsTotalsView.as_view(),
    ),
    path(
        "detailed-monitoring/status/",
        DetailedMonitoringStatusView.as_view(),
    ),
    path(
        "analysis/detailed-monitoring/status/",
        AnalysisDetailedMonitoringStatusView.as_view(),
    ),
    path(
        "sales/total-revenue/",
        TotalRevenueView.as_view(),
    ),
]
