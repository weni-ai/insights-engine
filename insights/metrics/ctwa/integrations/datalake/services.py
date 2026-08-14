from insights.metrics.ctwa.integrations.datalake.dataclass import CTWAConversionsData


MOCK_CTWA_CONVERSIONS_DATA = CTWAConversionsData(
    conversations_started=19400,
    conversations_qualified=7180,
    conversations_converted=2880,
)


class CTWADatalakeService:
    """
    CTWA conversions from Datalake.

    The real events query is not available yet; ``get_conversions_data``
    currently returns mocked counts.
    """

    def get_conversions_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> CTWAConversionsData:
        return MOCK_CTWA_CONVERSIONS_DATA
