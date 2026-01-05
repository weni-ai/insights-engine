import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class ChatsTimeMetricsClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.base_url = settings.CHATS_URL

    def retrieve_time_metrics(self, params: dict | None = None) -> dict:
        url = self.base_url + f"/v1/dashboard/{self.project.uuid}/time_metrics/"
        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def retrieve_time_metrics_for_analysis(self, params: dict | None = None) -> dict:
        url = (
            self.base_url
            + f"/v1/dashboard/{self.project.uuid}/time_metrics_for_analysis/"
        )
        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
