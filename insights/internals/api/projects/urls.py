from django.urls import path

from .views import UpdateProjectVTEXAccountView

app_name = "projects"

urlpatterns = [
    path(
        "<uuid:project_uuid>/vtex-account",
        UpdateProjectVTEXAccountView.as_view(),
        name="update_vtex_account",
    ),
]
