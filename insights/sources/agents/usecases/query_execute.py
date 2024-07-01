from insights.db.postgres.django.connection import dictfetchall, get_cursor
from insights.sources.agents.clients import (
    AgentsRESTClient,
    generate_sql_query,
)


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        return_format: str = None,
        project: object = None,
        user_email: str = None,
        *args,
        **kwargs
    ):
        if return_format == "select_input" or operation != "list":
            filters["project_id"] = str(project.uuid)
            query, params = generate_sql_query(filters=filters, query_type=operation)
            with get_cursor(db_name="chats") as cur:
                query_exec = cur.execute(query, params)
                query_results = dictfetchall(query_exec)
            paginated_results = {
                "next": None,
                "previous": None,
                "results": query_results,
            }
            return paginated_results  # parser(paginated_results)

        client = AgentsRESTClient(project=project)
        filters["user_request"] = user_email
        query_results = client.list(filters)

        nxt = query_results.get("next")
        nxt = None if nxt is None else nxt.split("?")[1]
        prev = query_results.get("previous")
        prev = None if prev is None else prev.split("?")[1]
        paginated_results = {
            "next": nxt,
            "previous": prev,
            "results": query_results.get("results"),
        }
        return paginated_results  # parser(paginated_results)
