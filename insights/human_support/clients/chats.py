from insights.core.requests import request_with_retry
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

    def csat_score_by_agents(
        self, project_uuid: str, params: dict | None = None
    ) -> dict:
        url = f"{self.url}/v1/internal/dashboard/{project_uuid}/csat-score-by-agents/"

        response = requests.get(
            url=url,
            headers=self.headers,
            params=params or {},
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

    def get_internal_rooms_v2(self, query_params: dict):
        response = request_with_retry(
            url=f"{self.url}/v2/internal/rooms/",
            headers=self.headers,
            params=query_params,
            method="GET",
            timeout=60,
            max_retries=3,
        )
        return response.json()
