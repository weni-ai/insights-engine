from uuid import UUID

from django.conf import settings

from insights.internals.base import InternalJWTAuthentication
from insights.metrics.ctwa.mocks import MOCK_CAMPAIGNS


class FlowsCampaignClient(InternalJWTAuthentication):
    """
    Client for Meta/CTWA campaigns stored in Flows.

    The Flows API is not available yet; ``list_campaigns`` currently returns
    mocked paginated data. Replace ``_mock_list_campaigns`` with a real HTTP
    call when the endpoint is ready.
    """

    project_uuid_field = "project_uuid"

    def __init__(self, project_uuid: str | UUID) -> None:
        self.project_uuid = str(project_uuid)
        self.url = f"{settings.FLOWS_URL}/api/v2/internals/campaigns.json"

    def list_campaigns(
        self,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        return self._mock_list_campaigns(
            search=search, page=page, page_size=page_size
        )

    def _mock_list_campaigns(
        self,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        results = MOCK_CAMPAIGNS
        if search:
            search_normalized = search.casefold()
            results = [
                campaign
                for campaign in results
                if search_normalized in campaign["name"].casefold()
            ]

        start = (page - 1) * page_size
        end = start + page_size

        return {
            "count": len(results),
            "results": results[start:end],
        }
