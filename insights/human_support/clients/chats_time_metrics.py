import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class ChatsTimeMetricsClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = (
            f"{settings.CHATS_URL}/v1/dashboard/{self.project.uuid}/time_metrics/"
        )

    def retrieve(self, params: dict | None = None) -> dict:
        response = requests.get(
            url=self.url,
            headers=self.headers,
            params=params or {},
        )
        response.raise_for_status()
        return response.json()
