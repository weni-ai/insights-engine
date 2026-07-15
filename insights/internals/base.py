import requests
from django.conf import settings

from insights.core.accessors import get_nested_attr


class InternalAuthentication:
    def get_module_token(self):
        request = requests.post(
            url=settings.OIDC_OP_TOKEN_ENDPOINT,
            data={
                "client_id": settings.OIDC_RP_CLIENT_ID,
                "client_secret": settings.OIDC_RP_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        # TODO: exception token None
        token = request.json().get("access_token")
        return f"Bearer {token}"

    @property
    def headers(self):
        return {
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": self.get_module_token(),
        }


class InternalJWTAuthentication:
    project_uuid_field = "project.uuid"

    def _get_project_uuid(self):
        return get_nested_attr(self, self.project_uuid_field)

    @property
    def headers(self):
        from insights.authentication.services.jwt_service import JWTService

        token = JWTService().generate_jwt_token(project_uuid=self._get_project_uuid())
        return {
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": f"Bearer {token}",
        }


class VtexAuthentication:
    pass
