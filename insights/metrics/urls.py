from django.urls import include, path

namespace = "metrics"

urlpatterns = [
    path("vtex/", include("insights.metrics.vtex.urls")),
    path("meta/", include("insights.metrics.meta.urls")),
    path("skills/", include("insights.metrics.skills.urls")),
    path("conversations/", include("insights.metrics.conversations.urls")),
    path("human-support/", include("insights.metrics.human_support.urls")),
]
