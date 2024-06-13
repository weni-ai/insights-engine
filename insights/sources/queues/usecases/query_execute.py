from insights.db.postgres.connection import dictfetchall, get_cursor
from insights.sources.queues.clients import generate_sql_query


class QueryExecutor:
    def execute(filters: dict, operation: str, parser: callable, *args, **kwargs):
        query, params = generate_sql_query(filters=filters, query_type=operation)
        with get_cursor(db_name="chats") as cur:
            query_exec = cur.execute(query, params)
            query_results = dictfetchall(query_exec)
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return parser(paginated_results)
