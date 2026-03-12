from django.urls import path, include
from rest_framework.routers import DefaultRouter

from insights.metrics.conversations.api.v2.views import ConversationsMetricsViewSetV2

router = DefaultRouter()
router.register(
    "",
    ConversationsMetricsViewSetV2,
    basename="conversations-v2",
)

urlpatterns = [
    path("", include(router.urls)),
]
