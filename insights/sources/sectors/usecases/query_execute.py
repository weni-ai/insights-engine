from insights.db.postgres.django.connection import dictfetchall, get_cursor
from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.sectors.clients import SectorSQLQueryGenerator
from insights.sources.sectors.filtersets import SectorFilterSet
from insights.sources.sectors.query_builder import SectorSQLQueryBuilder


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        query_generator = SectorSQLQueryGenerator(
            filter_strategy=PostgreSQLFilterStrategy,
            query_builder=SectorSQLQueryBuilder,
            filterset=SectorFilterSet,
            filters=filters,
            query_type=operation,
            query_kwargs=query_kwargs,
        )
        query, params = query_generator.generate()
        with get_cursor(db_name="chats") as cur:
            query_exec = cur.execute(query, params)
            query_results = dictfetchall(query_exec)
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return paginated_results  # parser(paginated_results)
