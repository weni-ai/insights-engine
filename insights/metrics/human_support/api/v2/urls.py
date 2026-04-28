from django.urls import path

from insights.metrics.human_support.api.v2.views import (
    DetailedMonitoringAgentsViewV2,
)

urlpatterns = [
    path(
        "detailed-monitoring/agents/",
        DetailedMonitoringAgentsViewV2.as_view(),
    ),
]
