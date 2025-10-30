import requests
from django.conf import settings
from insights.internals.base import InternalAuthentication


class ChatsClient(InternalAuthentication):
    def __init__(self) -> None:
        self.base_url = settings.CHATS_URL

    def csat_ratings(self, project_uuid: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}/v1/internal/dashboard/{project_uuid}/csat_ratings/"

        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
        )
        response.raise_for_status()

        return response.json()
