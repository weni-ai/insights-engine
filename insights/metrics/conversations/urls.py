from django.urls import path, include
from rest_framework.routers import DefaultRouter

from insights.metrics.conversations.views import ConversationsMetricsViewSet
from insights.metrics.conversations.reports.views import (
    AvailableWidgetsViewSet,
    ConversationsReportsViewSet,
)

router = DefaultRouter()
router.register("", ConversationsMetricsViewSet, basename="conversations")

urlpatterns = [
    path(
        "report/available-widgets/",
        AvailableWidgetsViewSet.as_view(),
        name="report-available-widgets",
    ),
    path("report/", ConversationsReportsViewSet.as_view(), name="conversations-report"),
    path("", include(router.urls)),
]
