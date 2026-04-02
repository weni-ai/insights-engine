from django.urls import include, path
from rest_framework.routers import DefaultRouter

from insights.dashboards.api.v2.viewsets import DashboardViewSetV2

router = DefaultRouter()
router.register(r"", DashboardViewSetV2, basename="dashboard-v2")

urlpatterns = [
    path("", include(router.urls)),
]
