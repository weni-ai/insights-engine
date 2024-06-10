from insights.sources.filters import BasicFilterStrategy
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder

relation_schema = {
    "agent": {"field_name": "user_id", "table_alias": "r"},
    "project": {"field_name": "uuid", "table_alias": "p"},
    "tag": {"field_name": "sectortag_id", "table_alias": "tg"},
    "sector": {"field_name": "uuid", "table_alias": "s"},
    "queue": {"field_name": "queue_id", "table_alias": "r"},
}


def get_joins_from_schema(field):
    joins = dict()
    if "sector" == field or "project" == field:
        joins["q"] = "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id"
    if "project" == field:
        joins["s"] = "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id"
        joins["p"] = "INNER JOIN public.projects_project AS p ON p.uuid=s.project_id"
    if "tag" == field:
        joins["tg"] = "INNER JOIN public.rooms_room_tags AS tg ON tg.room_id=r.uuid"

    return joins


def generate_sql_query(
    filters: dict,
    schema: dict = relation_schema,
    query_type: str = "count",
    query_kwargs: dict = {},
):
    strategy = BasicFilterStrategy()
    builder = RoomSQLQueryBuilder()

    for key, value in filters.items():
        table_alias = "r"
        if "__" in key:
            field, operation = key.split("__", 1)
        else:
            field, operation = key, "eq"

        if field in schema:
            f_schema = schema[field]
            builder.add_joins(get_joins_from_schema(field))
            field = f_schema["field_name"]
            table_alias = f_schema["table_alias"]
        builder.add_filter(strategy, field, operation, value, table_alias)
    builder.build_query()
    return getattr(builder, query_type)(**query_kwargs)
