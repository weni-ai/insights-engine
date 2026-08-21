import logging

from insights.metrics.ctwa.integrations.datalake.services import CTWADatalakeService
from insights.sources.meta.campaign.clients import FlowsCampaignClient

logger = logging.getLogger(__name__)

FLOWS_CAMPAIGN_PAGE_SIZE = 100


class CTWADashboardService:
    """
    CTWA dashboard metrics.

    Summary, conversions and performance by campaign come from Datalake
    (weni-ctwa-by-campaign). Organic conversations are conversational totals
    minus CTWA started. Currency is a default until a dedicated endpoint exists.
    Campaign filter uses campaign_source (same id as the Flows campaign list).
    Performance rows include label.headline from Flows (source_id match).
    """

    def __init__(
        self,
        datalake_service: CTWADatalakeService | None = None,
        campaign_client_class=FlowsCampaignClient,
    ):
        self.datalake_service = datalake_service or CTWADatalakeService()
        self.campaign_client_class = campaign_client_class

    def get_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> dict:
        data = self.datalake_service.get_summary_data(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            campaign=campaign,
        )
        return {
            "attributed_revenue": {
                "currency": data.currency,
                "value": data.attributed_revenue,
                "avg": data.avg_order_value,
            },
            "ctwa_conversations": data.ctwa_conversations,
            "organic_conversations": data.organic_conversations,
        }

    def get_conversions(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> dict:
        data = self.datalake_service.get_conversions_data(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            campaign=campaign,
        )
        started = data.conversations_started

        return {
            "conversations_started": {
                "total": started,
                "percentage": 100,
            },
            "conversations_qualified": {
                "total": data.conversations_qualified,
                "percentage": self._percentage(data.conversations_qualified, started),
            },
            "conversations_converted": {
                "total": data.conversations_converted,
                "percentage": self._percentage(data.conversations_converted, started),
            },
        }

    def get_performance_by_campaign(
        self,
        project_uuid: str,
        start_date,
        end_date,
        limit: int = 10,
        offset: int = 0,
        campaign: str | None = None,
    ) -> dict:
        data = self.datalake_service.get_performance_by_campaign(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            campaign=campaign,
        )
        headlines = self._headlines_by_source_id(project_uuid)
        for item in data.get("results", []):
            campaign_id = str(item.get("campaign") or "")
            item["label"] = {
                "headline": headlines.get(campaign_id) or "",
                "id": campaign_id,
            }
        return data

    def _headlines_by_source_id(self, project_uuid: str) -> dict[str, str]:
        try:
            client = self.campaign_client_class(project_uuid)
            headlines: dict[str, str] = {}
            offset = 0
            while True:
                payload = client.list_campaigns(
                    limit=FLOWS_CAMPAIGN_PAGE_SIZE,
                    offset=offset,
                )
                results = payload.get("results") or []
                for item in results:
                    source_id = str(item.get("uuid") or "")
                    if source_id:
                        headlines[source_id] = item.get("headline") or ""
                if len(results) < FLOWS_CAMPAIGN_PAGE_SIZE:
                    break
                offset += FLOWS_CAMPAIGN_PAGE_SIZE
            return headlines
        except Exception:
            logger.exception(
                "[ CTWADashboardService ] Failed to list campaign headlines for project %s",
                project_uuid,
            )
            return {}

    def _percentage(self, value: int, total: int) -> float:
        if not total:
            return 0
        return round((value / total) * 100, 1)
