from insights.db.postgres.psycopg.connection import get_cursor
from insights.sources.flows.clients import generate_sql_query


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        project: object,
        *args,
        **kwargs
    ):
        filters["project"] = str(project.uuid)
        query, params = generate_sql_query(filters=filters, query_type=operation)
        with get_cursor(db_name="flows") as cur:
            query_results = cur.execute(query, params).fetchall()
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return paginated_results  # parser(paginated_results)
