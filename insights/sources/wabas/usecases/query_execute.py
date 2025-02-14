from insights.sources.wabas.client import WeniIntegrationsClient


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        client = WeniIntegrationsClient(project_uuid=filters.get("project"))
        tokens = client.get_wabas_for_project()

        return tokens
