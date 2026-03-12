from django.urls import include, path

from insights.metrics.conversations.api.v1.urls import internal_router

app_name = "internal_api"

urlpatterns = [
    path("users/", include("insights.internals.api.users.urls", namespace="users")),
    path("metrics/conversations/", include(internal_router.urls)),
]
