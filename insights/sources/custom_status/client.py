import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class CustomStatusRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.base_url = f"{settings.CHATS_URL}"
        self.timeout = 30

    def list_custom_status(self, query_filters: dict):
        url = f"{self.base_url}/v1/internal/dashboard/{self.project.uuid}/custom_status_agent/"

        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")

        response = requests.get(
            url=url, headers=self.headers, params=query_filters, timeout=self.timeout
        )
        return response.json()

    def list_custom_status_types(self):
        url = f"{self.base_url}/v1/custom_status_type/"
        response = requests.get(
            url=url,
            headers=self.headers,
            params={"project": str(self.project.uuid)},
            timeout=self.timeout,
        )
        data = response.json()
        return [
            {"uuid": item["uuid"], "name": item["name"]}
            for item in data.get("results", [])
        ]

    def list_custom_status_by_agent(self, query_filters: dict):
        url = f"{self.base_url}/v1/internal/dashboard/{self.project.uuid}/custom-status-by-agent/"
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")

        response = requests.get(
            url=url, headers=self.headers, params=query_filters, timeout=self.timeout
        )
        return response.json()
