import requests

from django.conf import settings
from rest_framework import status

from insights.internals.base import InternalAuthentication
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound
from insights.sources.vtexcredentials.typing import VtexCredentialsDTO


class AuthRestClient(InternalAuthentication):
    def __init__(self, project: str) -> None:
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/vtex/integration-details/{project}"

    def get_vtex_auth(self) -> VtexCredentialsDTO:
        response = requests.get(url=self.url, headers=self.headers)

        if not status.is_success(response.status_code):
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise VtexCredentialsNotFound(
                    f"Credentials not found for project {self.project}"
                )

            raise Exception("Failed to get VTEX credentials")

        tokens = response.json()
        credentials = {
            "app_key": tokens["app_key"],
            "app_token": tokens["app_token"],
            "domain": tokens["domain"],
        }
        return credentials
