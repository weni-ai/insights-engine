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
    CTWA dashboard summary.

    Data source is still undefined; ``get_data`` currently returns mocked
    values matching the dashboard contract.
    """

    def get_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> dict:
        return dict(MOCK_CTWA_DATA)
