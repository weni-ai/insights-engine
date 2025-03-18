from django.urls import include, path

app_name = "internal_api"

urlpatterns = [
    path("users/", include("insights.internals.api.users.urls", namespace="users")),
]
