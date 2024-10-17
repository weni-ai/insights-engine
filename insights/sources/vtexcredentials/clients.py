import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class AuthRestClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/vtex/integration-details/{project}"

    def get_vtex_auth(self):
        # response = requests.get(url=self.url, headers=self.headers)
        # print("url", self.url)
        # print("RESPONSE", response)
        # tokens = response.json()
        # print("TOKEN", tokens)
        # credentials = {
        #     "app_key": tokens["app_key"],
        #     "app_token": tokens["app_token"],
        #     "domain": tokens["domain"],
        # }
        # print("credenciais")
        return {}
