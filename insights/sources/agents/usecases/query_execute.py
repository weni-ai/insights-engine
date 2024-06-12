from insights.db.postgres.connection import dictfetchall, get_cursor
from insights.sources.agents.clients import (
    AgentsRESTClient,
    generate_sql_query,
)


class QueryExecutor:
    def execute(
        filters: dict,
        action: str,
        parser: callable,
        return_format: str = None,
        project: object = None,
        user_email: str = None,
        *args,
        **kwargs
    ):
        if return_format == "select_input" or action != "list":
            filters["project_id"] = str(project.uuid)
            filters["user_request"] = user_email
            query, params = generate_sql_query(filters=filters, query_type=action)
            with get_cursor(db_name="chats") as cur:
                query_results = dictfetchall(cur.execute(query, params).fetchall())
            paginated_results = {
                "next": None,
                "previous": None,
                "results": query_results,
            }
            return parser(paginated_results)
        client = AgentsRESTClient(project=project)
        query_results = client.list(filters)
        paginated_results = {
            "next": query_results.get("next").split("?")[1],
            "previous": query_results.get("previous").split("?")[1],
            "results": query_results.get("results"),
        }