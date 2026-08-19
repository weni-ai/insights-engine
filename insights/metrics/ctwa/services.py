from insights.metrics.ctwa.integrations.datalake.services import CTWADatalakeService


class CTWADashboardService:
    """
    CTWA dashboard metrics.

    Summary, conversions and performance by campaign come from Datalake
    (weni-ctwa-by-campaign). Organic conversations are conversational totals
    minus CTWA started. Currency is a default until a dedicated endpoint exists.
    Campaign filter uses campaign_source (same id as the Flows campaign list).
    """

    def __init__(self, datalake_service: CTWADatalakeService | None = None):
        self.datalake_service = datalake_service or CTWADatalakeService()

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
        return self.datalake_service.get_performance_by_campaign(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            campaign=campaign,
        )

    def _percentage(self, value: int, total: int) -> float:
        if not total:
            return 0
        return round((value / total) * 100, 1)
