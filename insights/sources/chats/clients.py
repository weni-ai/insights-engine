from django.conf import settings

from insights.internals.base import InternalAuthentication
from insights.core.requests import request_with_retry


class ChatsRESTClient(InternalAuthentication):
    def __init__(self):
        self.base_url = f"{settings.CHATS_URL}"

    def get_project(self, project_uuid: str) -> dict:
        response = request_with_retry(
            url=f"{self.base_url}/v1/internal/project/{project_uuid}/",
            headers=self.headers,
            params={},
            method="GET",
            timeout=60,
            max_retries=3,
        )

        return response.json()
