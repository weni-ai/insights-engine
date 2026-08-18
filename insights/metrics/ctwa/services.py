from insights.metrics.ctwa.integrations.datalake.services import CTWADatalakeService

MOCK_CTWA_DATA = {
    "attributed_revenue": {
        "currency": "USD",
        "value": 1030000,
        "avg": 359,
    },
    "ctwa_conversations": 19400,
    "organic_conversations": 22800,
}


class CTWADashboardService:
    """
    CTWA dashboard metrics.

    Summary data source is still undefined; ``get_data`` currently returns
    mocked values matching the dashboard contract. Conversions are expected
    to come from Datalake and are mocked until the events query is available.
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
        return dict(MOCK_CTWA_DATA)

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

    def _percentage(self, value: int, total: int) -> float:
        if not total:
            return 0
        return round((value / total) * 100, 1)
