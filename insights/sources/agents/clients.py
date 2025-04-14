import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication
from insights.sources.clients import GenericSQLQueryGenerator


class AgentSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"


class AgentsRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = (
            f"{settings.CHATS_URL}/v1/internal/dashboard/{self.project.uuid}/agent/"
        )

    def list(self, query_filters: dict):
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")
        
        
        print(query_filters)
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return response.json()
