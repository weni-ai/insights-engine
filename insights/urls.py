"""
URL configuration for insights project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from weni_feature_flags.views import FeatureFlagsWebhookView

from insights.dashboards.viewsets import DashboardViewSet
from insights.feature_flags.views import FeatureFlagsViewSet
from insights.projects.viewsets import ProjectViewSet
from insights.widgets.viewsets import WidgetViewSet
from insights.feature_flags.integrations.growthbook.views import GrowthbookWebhook
from insights.feature_flags.views import FeatureFlagsViewSet

urlpatterns = []


router = DefaultRouter()
router.register(r"widgets", WidgetViewSet, basename="widget")
router.register(r"dashboards", DashboardViewSet, basename="dashboard")
router.register(r"projects", ProjectViewSet, basename="project")
# router.register(r"growthbook", GrowthbookWebhook, basename="growthbook_webhook")
router.register(r"feature_flags", FeatureFlagsViewSet, basename="feature_flags")

urlpatterns += [
    path("", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("v1/metrics/", include("insights.metrics.urls")),
    path(
        "v1/internal/", include("insights.internals.api.urls", namespace="internal_api")
    ),
    path(
        "v1/growthbook/",
        FeatureFlagsWebhookView.as_view(),
        name="feature_flags_webhook",
    ),
    path("v1/", include(router.urls)),
]

if settings.ADMIN_ENABLED is True:
    from django.contrib import admin

    urlpatterns += [
        path("admin/", admin.site.urls),
    ]
