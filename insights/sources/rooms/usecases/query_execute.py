from insights.db.postgres.connection import dictfetchall, get_cursor
from insights.sources.rooms.clients import RoomRESTClient, generate_sql_query


class QueryExecutor:
    def execute(
        filters: dict, action: str, parser: callable, project: object, *args, **kwargs
    ):
        if action == "list":
            client = RoomRESTClient(project=project)
            query_results = client.list(filters)
            paginated_results = {
                "next": query_results.get("next").split("?")[1],
                "previous": query_results.get("previous").split("?")[1],
                "results": query_results.get("results"),
            }
            query, params = generate_sql_query(filters=filters, query_type=action)
        with get_cursor(db_name="chats") as cur:
            query_exec = cur.execute(query, params)
            query_results = dictfetchall(query_exec)
        paginated_results = {"next": None, "previous": None, "results": query_results}
        return parser(paginated_results)
