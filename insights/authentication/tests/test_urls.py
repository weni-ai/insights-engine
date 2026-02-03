from django.urls import path
from insights.authentication.tests.test_authentication import MockJWTAuthenticationView

urlpatterns = [
    path(
        "jwt-authentication/",
        MockJWTAuthenticationView.as_view(),
        name="jwt-authentication-view",
    ),
]
