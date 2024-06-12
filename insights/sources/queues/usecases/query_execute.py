from insights.db.postgres.connection import dictfetchall, get_cursor
from insights.sources.queues.clients import generate_sql_query


class QueryExecutor:
    def execute(filters: dict, action: str, parser: callable, *args, **kwargs):
        query, params = generate_sql_query(filters=filters, query_type=action)
        with get_cursor(db_name="chats") as cur:
            query_results = dictfetchall(cur.execute(query, params).fetchall())
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return parser(paginated_results)
