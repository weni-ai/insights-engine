from insights.internals.base import InternalAuthentication
from django.conf import settings

import requests


class ChatsClient(InternalAuthentication):
    def __init__(self):
        self.url = settings.CHATS_URL

    def get_contacts(self, query_params: dict):
        url = f"{self.url}/v1/internal/contacts/"
        response = requests.get(
            url, headers=self.headers, params=query_params, timeout=60
        )
        response.raise_for_status()

        return response.json()

    def get_protocols(self, query_params: dict):
        url = f"{self.url}/v1/internal/rooms/protocols/"
        response = requests.get(
            url, headers=self.headers, params=query_params, timeout=60
        )
        response.raise_for_status()

        return response.json()

    def csat_ratings(self, project_uuid: str, params: dict | None = None) -> dict:
        url = f"{self.url}/v1/internal/dashboard/{project_uuid}/csat_ratings/"

        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
        )
        response.raise_for_status()

        return response.json()
