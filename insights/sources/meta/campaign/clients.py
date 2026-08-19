from uuid import UUID

import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication


class FlowsCampaignClient(InternalAuthentication):
    """
    Client for CTWA referral sources stored in Flows.
    """

    def __init__(self, project_uuid: str | UUID) -> None:
        self.project_uuid = str(project_uuid)
        self.url = f"{settings.FLOWS_URL}/api/v2/internals/ctwa_referral_sources"

    def list_campaigns(
        self,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        params = {
            "project_uuid": self.project_uuid,
            "limit": page_size,
            "offset": (page - 1) * page_size,
            "after": settings.CTWA_CAMPAIGNS_AFTER,
        }
        if search:
            params["search"] = search

        response = requests.get(
            url=self.url,
            headers=self.headers,
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return self._parse_payload(response.json())

    def _parse_payload(self, payload: dict) -> dict:
        results = [
            self._parse_campaign(item) for item in payload.get("results", [])
        ]
        return {
            "count": payload.get("count", len(results)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": results,
        }

    def _parse_campaign(self, item: dict) -> dict:
        source_id = item.get("source_id")
        campaign_id = str(source_id) if source_id is not None else str(item.get("id", ""))
        return {
            "name": item.get("headline") or source_id or "",
            "uuid": campaign_id,
        }
