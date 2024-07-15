from insights.db.postgres.psycopg.connection import get_cursor
from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.flows.clients import FlowSQLQueryGenerator
from insights.sources.flows.filtersets import FlowsFilterSet
from insights.sources.flows.query_builder import FlowSQLQueryBuilder


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        query_generator = FlowSQLQueryGenerator(
            filter_strategy=PostgreSQLFilterStrategy,
            query_builder=FlowSQLQueryBuilder,
            filterset=FlowsFilterSet,
            filters=filters,
            query_type=operation,
            query_kwargs=query_kwargs,
        )
        query, params = query_generator.generate()

        with get_cursor(db_name="flows") as cur:
            query_results = cur.execute(query, params).fetchall()
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return paginated_results
