from django.urls import include, path

namespace = "metrics"

urlpatterns = [
    path("vtex/", include("insights.metrics.vtex.urls")),
    path("meta/", include("insights.metrics.meta.urls")),
]
