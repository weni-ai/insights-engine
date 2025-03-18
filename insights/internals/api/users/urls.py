from django.urls import path

from .views import ChangeUserLanguageView

app_name = "users"

urlpatterns = [
    path(
        "change-language/",
        ChangeUserLanguageView.as_view(),
        name="change_language",
    ),
]
