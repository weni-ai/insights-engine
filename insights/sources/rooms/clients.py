import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication
from insights.sources.filters import PostgreSQLFilterStrategy
from insights.sources.rooms.filters import RoomFilterSet
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder


def generate_sql_query(
    filters: dict,
    filterset_class=RoomFilterSet,
    query_type: str = "count",
    query_kwargs: dict = {},
):
    strategy = PostgreSQLFilterStrategy()
    builder = RoomSQLQueryBuilder()
    filterset = filterset_class()

    for key, value in filters.items():
        if "__" in key:
            field, operation = key.split("__", 1)
        elif type(value) is list:
            field = key.split("__", 1)[0]
            operation = "in"
        else:
            field, operation = key, "eq"
        field_object = filterset.get_field(field)
        if field_object is None:
            continue
        source_field = field_object.source_field
        join_clause = field_object.join_clause
        builder.add_joins(join_clause)
        builder.add_filter(
            strategy, source_field, operation, value, field_object.table_alias
        )
    builder.build_query()

    return getattr(builder, query_type)(**query_kwargs)


class RoomRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/internal/rooms/"

    def list(self, query_filters: dict):
        query_filters["project"] = str(self.project.uuid)

        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        return response.json()
