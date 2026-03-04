from urllib.parse import urlencode

from django.conf import settings
from django.contrib import auth
from django.shortcuts import redirect, resolve_url
from django.utils.module_loading import import_string

from insights.authentication.authentication import WeniOIDCAuthenticationBackend


def admin_oidc_login(request):
    return redirect("oidc_authentication_init")


def get_oidc_logout_url(request):
    end_session_endpoint = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
    redirect_target = resolve_url(getattr(settings, "LOGOUT_REDIRECT_URL", "/"))

    if not end_session_endpoint:
        return request.build_absolute_uri(redirect_target)

    params = {
        "post_logout_redirect_uri": request.build_absolute_uri(redirect_target),
    }

    id_token = request.session.get("oidc_id_token")

    if id_token:
        params["id_token_hint"] = id_token

    client_id = getattr(settings, "OIDC_RP_CLIENT_ID", "")

    if client_id:
        params["client_id"] = client_id

    return f"{end_session_endpoint}?{urlencode(params)}"


def admin_oidc_logout(request):
    """
    Logout view for the admin. When OIDC is enabled and OIDC_OP_LOGOUT_URL_METHOD
    is set, logs out the Django user and redirects to the IdP end-session endpoint
    (so the user is logged out of Keycloak as well). Otherwise redirects to the
    default admin logout.
    """
    logout_url_method = getattr(settings, "OIDC_OP_LOGOUT_URL_METHOD", "")
    if logout_url_method and request.user.is_authenticated:
        logout_url = import_string(logout_url_method)(request)
        auth.logout(request)
        return redirect(logout_url)
    auth.logout(request)
    return redirect(getattr(settings, "LOGOUT_REDIRECT_URL", "/admin/"))


class AdminOIDCAuthenticationBackend(WeniOIDCAuthenticationBackend):
    """
    OIDC backend for Django admin. Only pre-existing staff users can log in.
    """

    def filter_users_by_claims(self, claims):
        users = super().filter_users_by_claims(claims)
        return users.filter(is_staff=True)

    def create_user(self, claims):
        return None
