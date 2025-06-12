from django.urls import path, include
from rest_framework.routers import DefaultRouter

from insights.metrics.conversations.views import ConversationsMetricsViewSet

router = DefaultRouter()
router.register("", ConversationsMetricsViewSet, basename="conversations")
router.register(r"", ConversationsMetricsViewSet, basename="conversations")

urlpatterns = [
    path("", include(router.urls)),
]
