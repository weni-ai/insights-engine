import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class CustomStatusRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/dashboard/{self.project.uuid}/custom_status_agent/"

    def list(self, query_filters: dict):
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")

        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return response.json()
