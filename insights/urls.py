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

from insights.dashboards.viewsets import DashboardViewSet
from insights.projects.viewsets import ProjectViewSet
from insights.widgets.viewsets import WidgetListUpdateViewSet

urlpatterns = []


router = DefaultRouter()
router.register(r"widgets", WidgetListUpdateViewSet, basename="widget")
router.register(r"dashboards", DashboardViewSet, basename="dashboard")
router.register(r"projects", ProjectViewSet, basename="project")

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
    path("v1/", include(router.urls)),
]

if settings.ADMIN_ENABLED is True:
    from django.contrib import admin

    urlpatterns += [
        path("admin/", admin.site.urls),
    ]
