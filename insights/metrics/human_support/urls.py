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
        "volume-by-queue/",
        VolumeByQueueView.as_view(),
    ),
    path(
        "analysis/volume-by-queue/",
        AnalysisVolumeByQueueView.as_view(),
    ),
    path(
        "volume-by-tag/",
        VolumeByTagView.as_view(),
    ),
    path(
        "analysis/volume-by-tag/",
        AnalysisVolumeByTagView.as_view(),
    ),
]
