from insights.sources.filters import BasicFilterStrategy
from insights.sources.sectors.query_builder import SectorSQLQueryBuilder


def generate_sql_query(
    filters: dict,
    query_type: str = "list",
    query_kwargs: dict = {},
):
    strategy = BasicFilterStrategy()
    builder = SectorSQLQueryBuilder()

    for key, value in filters.items():
        table_alias = "s"
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
