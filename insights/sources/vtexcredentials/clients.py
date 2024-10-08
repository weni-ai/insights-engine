import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class AuthRestClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/vtex/integration-details/{self.project.uuid}"

    def get_vtex_auth(self):
        response = requests.get(url=self.url, headers=self.headers)
        tokens = response.json()

        credentials = {"app_key": tokens["KEY"], "app_token": tokens["TOKEN"]}

        return credentials
