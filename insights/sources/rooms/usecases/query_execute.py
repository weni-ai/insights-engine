from insights.db.postgres.connection import dictfetchall, get_cursor
from insights.sources.rooms.clients import RoomRESTClient, generate_sql_query


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        project: object,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        if operation == "list":
            client = RoomRESTClient(project=project)
            query_results = client.list(filters)
            nxt = (query_results.get("next"),)
            nxt = (None if nxt is None else nxt.split("?")[1],)
            prev = (query_results.get("previous"),)
            prev = (None if prev is None else prev.split("?")[1],)
            paginated_results = {
                "next": nxt,
                "previous": prev,
                "results": query_results.get("results"),
            }
            return paginated_results  # parser(paginated_results)
        query, params = generate_sql_query(
            filters=filters, query_type=operation, query_kwargs=query_kwargs
        )
        with get_cursor(db_name="chats") as cur:
            query_exec = cur.execute(query, params)
            query_results = dictfetchall(query_exec)
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return paginated_results  # parser(paginated_results)
