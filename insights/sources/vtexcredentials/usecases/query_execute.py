from insights.sources.vtexcredentials.clients import AuthRestClient


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        client = AuthRestClient(project=filters["project"])
        tokens = client.get_vtex_auth()
        return tokens
