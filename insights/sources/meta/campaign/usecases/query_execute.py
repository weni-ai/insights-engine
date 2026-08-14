from insights.sources.base import BaseQueryExecutor
from insights.sources.meta.campaign.clients import FlowsCampaignClient


class QueryExecutor(BaseQueryExecutor):
    @classmethod
    def execute(
        cls,
        filters: dict,
        operation: str = "list",
        parser: callable = None,
        query_kwargs: dict = None,
        *args,
        **kwargs,
    ):
        project_uuid = filters.get("project")
        client = FlowsCampaignClient(project_uuid=project_uuid)
        return client.list_campaigns(
            search=filters.get("search"),
            page=filters.get("page", 1),
            page_size=filters.get("page_size", 10),
        )
