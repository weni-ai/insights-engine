from django.urls import path, include
from rest_framework.routers import DefaultRouter

from insights.metrics.conversations.views import ConversationsMetricsViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationsMetricsViewSet, basename="conversations")

urlpatterns = [
    path("", include(router.urls)),
]
