from django.conf import settings

from insights.internals.base import InternalJWTAuthentication
from insights.core.requests import request_with_retry


class ChatsRESTClient(InternalJWTAuthentication):
    def __init__(self, project):
        self.project = project
        self.base_url = f"{settings.CHATS_URL}"

    def get_project(self) -> dict:
        response = request_with_retry(
            url=f"{self.base_url}/v1/internal/project/{self.project.uuid}/",
            headers=self.headers,
            params={},
            method="GET",
            timeout=60,
            max_retries=3,
        )

        return response.json()

    def get_agents(self, query_filters: dict) -> dict:
        response = request_with_retry(
            url=f"{self.base_url}/v2/internal/dashboard/{self.project.uuid}/agent/",
            headers=self.headers,
            params=query_filters,
            method="GET",
            timeout=60,
            max_retries=3,
        )
        return response.json()

    def get_status_by_agent(self, query_filters: dict) -> dict:
        response = request_with_retry(
            url=f"{self.base_url}/v2/internal/dashboard/{self.project.uuid}/custom-status-by-agent/",
            headers=self.headers,
            params=query_filters,
            method="GET",
            timeout=60,
            max_retries=3,
        )
        return response.json()
