from django.urls import path

from .views import (
    DetailedMonitoringOnGoingView,
    DetailedMonitoringAwaitingView,
    DetailedMonitoringAgentsView,
    DetailedMonitoringStatusView,
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
        "detailed-monitoring/status/",
        DetailedMonitoringStatusView.as_view(),
    ),
]
