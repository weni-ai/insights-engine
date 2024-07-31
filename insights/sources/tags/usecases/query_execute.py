from insights.db.postgres.django.connection import dictfetchall, get_cursor
from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.tags.clients import TagSQLQueryGenerator
from insights.sources.tags.filtersets import TagFilterSet
from insights.sources.tags.query_builder import TagSQLQueryBuilder


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        query_generator = TagSQLQueryGenerator(
            filter_strategy=PostgreSQLFilterStrategy,
            query_builder=TagSQLQueryBuilder,
            filterset=TagFilterSet,
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
