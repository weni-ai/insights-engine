from insights.sources.integrations.clients import WeniIntegrationsClient


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        client = WeniIntegrationsClient()
        wabas = client.get_wabas_for_project(filters.get("project"))

        return wabas
