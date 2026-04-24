from django.urls import include, path
from rest_framework.routers import DefaultRouter

from insights.feature_flags.views import FeatureFlagsViewSet

router = DefaultRouter()
router.register(r"feature_flags", FeatureFlagsViewSet, basename="feature_flags")

urlpatterns = [
    path("v1/", include(router.urls)),
]
