import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from insights.users.usecases import CreateUserUseCase

import requests
from django.conf import settings

LOGGER = logging.getLogger("weni_django_oidc")

User = get_user_model()


def check_module_permission(claims, user):
    if claims.get("can_communicate_internally", False):
        content_type = ContentType.objects.get_for_model(User)
        permission, created = Permission.objects.get_or_create(
            codename="can_communicate_internally",
            name="can communicate internally",
            content_type=content_type,
        )
        if not user.has_perm("accounts.can_communicate_internally"):
            user.user_permissions.add(permission)
        return True
    return False


class WeniOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        verified = super(WeniOIDCAuthenticationBackend, self).verify_claims(claims)
        return verified

    def get_username(self, claims):
        username = claims.get("preferred_username")
        if username:
            return username
        return super(WeniOIDCAuthenticationBackend, self).get_username(claims=claims)

    def update_user(self, user, claims):
        user.name = claims.get("name", "")
        user.email = claims.get("email", "")
        user.save()

        return user

    def create_user(self, claims):
        email = claims.get("email")
        user = CreateUserUseCase().create_user(email)

        check_module_permission(claims, user)

        return user


class FlowsInternalAuthentication:
    def get_module_token(self):
        request = requests.post(
            url=settings.OIDC_OP_TOKEN_ENDPOINT,
            data={
                "client_id": settings.OIDC_RP_CLIENT_ID,
                "client_secret": settings.OIDC_RP_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        token = request.json().get("access_token")
        return f"Bearer {token}"

    @property
    def headers(self):
        return {
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": self.get_module_token(),
        }

    def get_flows_user_api_token(self, project_uuid: str, user_email: str):
        params = dict(project=project_uuid, user=user_email)
        response = requests.get(
            url=f"{settings.FLOWS_URL}/api/v2/internals/users/api-token",
            params=params,
            headers=self.headers,
        )
        return response
