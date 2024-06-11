import requests
from django.conf import settings
from django.db import connections

from insights.sources.agents.query_builder import AgentSQLQueryBuilder
from insights.sources.filters import BasicFilterStrategy


def secondary_dbs_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


class AgentsRESTClient:
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/internal/dashboard/{self.project}/agent/"

    def headers(self, internal_token):
        return {"Authorization": f"Bearer {internal_token}"}

    def list(self, query_filters: dict):
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
        else:
            field, operation = key, "eq"
        builder.add_filter(strategy, field, operation, value, table_alias)
    builder.build_query()
    return getattr(builder, query_type)(**query_kwargs)


class AgentsSQLClient:
    db_name = "chats"

    def list(self, query_filters: dict = None, *args, **kwargs):
        query = generate_sql_query(query_filters)
        return secondary_dbs_execute_query(db_name=self.db_name, query=query)
