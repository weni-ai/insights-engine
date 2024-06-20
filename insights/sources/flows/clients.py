from insights.sources.filters import BasicFilterStrategy
from insights.sources.flows.query_builder import FlowSQLQueryBuilder


relation_schema = {
    "project": {"field_name": "proj_uuid", "table_alias": "o"},
}


def get_joins_from_schema(field):
    joins = dict()
    if "project" == field:
        joins["q"] = "INNER JOIN public.orgs_org AS o ON o.id=f.org_id"

    return joins


def generate_sql_query(
    filters: dict,
    schema: dict = relation_schema,
    query_type: str = "count",
    query_kwargs: dict = {},
):
    strategy = BasicFilterStrategy()
    builder = FlowSQLQueryBuilder()

    for key, value in filters.items():
        table_alias = "r"
        if "__" in key:
            field, operation = key.split("__", 1)
        elif type(value) is list:
            field = key.split("__", 1)[0]
            operation = "in"
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
