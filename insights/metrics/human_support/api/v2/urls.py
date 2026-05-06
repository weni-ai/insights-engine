from django.urls import path

from insights.metrics.human_support.api.v2.views import (
    DetailedMonitoringAgentsViewV2,
    DetailedMonitoringStatusViewV2,
    AnalysisDetailedMonitoringStatusViewV2,
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
]
