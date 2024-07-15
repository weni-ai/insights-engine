from insights.db.postgres.django.connection import dictfetchall, get_cursor
from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.queues.clients import QueueSQLQueryGenerator
from insights.sources.queues.filtersets import QueueFilterSet
from insights.sources.queues.query_builder import QueueSQLQueryBuilder


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        query_generator = QueueSQLQueryGenerator(
            filter_strategy=PostgreSQLFilterStrategy,
            query_builder=QueueSQLQueryBuilder,
            filterset=QueueFilterSet,
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
