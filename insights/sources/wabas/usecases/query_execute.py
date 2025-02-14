from insights.sources.wabas.clients import WeniIntegrationsClient


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
        wabas = client.get_wabas_for_project()

        return wabas
