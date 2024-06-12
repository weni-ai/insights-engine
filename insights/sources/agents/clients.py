import requests
from django.conf import settings

from insights.sources.agents.query_builder import AgentSQLQueryBuilder
from insights.sources.filters import BasicFilterStrategy


class AgentsRESTClient:
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/internal/dashboard/{self.project}/agent/"

    def headers(self, internal_token):
        return {"Authorization": f"Bearer {internal_token}"}

    def list(self, query_filters: dict):
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.get("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.get("created_on__lte")
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return response.json()


def generate_sql_query(
    filters: dict,
    query_type: str = "list",
    query_kwargs: dict = {},
):
    strategy = BasicFilterStrategy()
    builder = AgentSQLQueryBuilder()

    for key, value in filters.items():
        table_alias = "pp"
        if "__" in key:
            field, operation = key.split("__", 1)
        elif type(value) is list:
            field = key.split("__", 1)[0]
            operation = "in"
        else:
            field, operation = key, "eq"
        builder.add_filter(strategy, field, operation, value, table_alias)
    builder.build_query()
    return getattr(builder, query_type)(**query_kwargs)
