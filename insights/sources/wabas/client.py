from django.conf import settings
import requests

from insights.internals.base import InternalAuthentication


class WeniIntegrationsClient(InternalAuthentication):
    def __init__(self, project_uuid: str):
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/wpp-cloud/list_wpp-cloud/{project_uuid}"

    def get_wabas_for_project(self):
        response = requests.get(url=self.url, headers=self.headers, timeout=60)
        wabas = response.json().get("data")

        return wabas
