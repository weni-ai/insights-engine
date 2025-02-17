from django.urls import include, path
from rest_framework import routers

from insights.metrics.vtex.views import VtexOrdersViewSet

namespace = "insights_metrics_vtex"

router = routers.DefaultRouter()
router.register(r"orders", VtexOrdersViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
]
