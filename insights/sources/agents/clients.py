import requests
from django.conf import settings

from insights.sources.agents.query_builder import AgentSQLQueryBuilder
from insights.sources.filters import BasicFilterStrategy


class AgentsRESTClient:
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/dashboard/{self.project}/agent/"

    def headers(self, internal_token):
        return {"Authorization": f"Bearer {internal_token}"}

    def list(self, query_filters: dict):
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters.__dict__
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
        table_alias = "r"
        if "__" in key:
            field, operation = key.split("__", 1)
        else:
            field, operation = key, "eq"
        builder.add_filter(strategy, field, operation, value, table_alias)
    builder.build_query()
    return getattr(builder, query_type)(**query_kwargs)
