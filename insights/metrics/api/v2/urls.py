from django.urls import path, include

namespace = "insights_metrics_v2"

urlpatterns = [
    path("conversations/", include("insights.metrics.conversations.api.v2.urls")),
]
