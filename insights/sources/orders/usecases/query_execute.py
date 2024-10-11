from insights.sources.orders.clients import VtexOrdersRestClient


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        auth_params: dict = {},
        *args,
        **kwargs
    ):
        client = VtexOrdersRestClient(auth_params=auth_params)
        list_data = client.list(query_filters=filters)

        return list_data
