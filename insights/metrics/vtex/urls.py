from django.urls import include, path
from rest_framework import routers

from insights.metrics.vtex.views import InternalVTEXOrdersViewSet, VtexOrdersViewSet

namespace = "insights_metrics_vtex"

router = routers.DefaultRouter()
router.register(r"orders", VtexOrdersViewSet, basename="orders")
router.register(
    r"internal/orders", InternalVTEXOrdersViewSet, basename="internal-orders"
)

urlpatterns = [
    path("", include(router.urls)),
]
