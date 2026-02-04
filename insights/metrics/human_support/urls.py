from django.urls import path

from .views import (
    DetailedMonitoringOnGoingView,
    DetailedMonitoringAwaitingView,
    DetailedMonitoringAgentsView,
    DetailedMonitoringStatusView,
    AnalysisDetailedMonitoringStatusView,
    VolumeByQueueView,
    AnalysisVolumeByQueueView,
    VolumeByTagView,
    AnalysisVolumeByTagView,
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
    path(
        "analysis/detailed-monitoring/status/",
        AnalysisDetailedMonitoringStatusView.as_view(),
    ),
    path(
        "queue_volume/",
        VolumeByQueueView.as_view(),
    ),
    path(
        "analysis/queue_volume/",
        AnalysisVolumeByQueueView.as_view(),
    ),
    path(
        "tags_volume/",
        VolumeByTagView.as_view(),
    ),
    path(
        "analysis/tags_volume/",
        AnalysisVolumeByTagView.as_view(),
    ),
]
