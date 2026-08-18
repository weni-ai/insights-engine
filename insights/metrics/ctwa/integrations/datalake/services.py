from insights.metrics.ctwa.integrations.datalake.dataclass import (
    CTWAConversionsData,
    CTWASummaryData,
)
from insights.metrics.ctwa.mocks import (
    MOCK_CURRENCY,
    MOCK_ORGANIC_CONVERSATIONS,
    aggregate_campaigns,
    filter_campaigns,
)


class CTWADatalakeService:
    """
    CTWA metrics from Datalake.

    The real events query is not available yet; methods currently return
    mocked data derived from the shared campaign list.
    """

    def get_summary_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> CTWASummaryData:
        totals = aggregate_campaigns(campaign)
        return CTWASummaryData(
            currency=MOCK_CURRENCY,
            attributed_revenue=totals["revenue"],
            avg_order_value=totals["avg"],
            ctwa_conversations=totals["conversations"],
            organic_conversations=MOCK_ORGANIC_CONVERSATIONS,
        )

    def get_conversions_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> CTWAConversionsData:
        totals = aggregate_campaigns(campaign)
        return CTWAConversionsData(
            conversations_started=totals["conversations"],
            conversations_qualified=totals["qualified"],
            conversations_converted=totals["conversions"],
        )

    def get_performance_by_campaign(
        self,
        project_uuid: str,
        start_date,
        end_date,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        rows = filter_campaigns()
        page = rows[offset : offset + limit]
        return {
            "currency": MOCK_CURRENCY,
            "count": len(rows),
            "results": [
                {
                    "campaign": row["campaign"],
                    "conversations": row["conversations"],
                    "qualified": row["qualified"],
                    "conversions": row["conversions"],
                    "revenue": row["revenue"],
                }
                for row in page
            ],
        }
