from datetime import date, datetime, time
from uuid import UUID

from django.conf import settings
from weni_datalake_sdk.clients.redshift.ctwa import get_ctwa_by_campaign

from insights.metrics.ctwa.integrations.datalake.dataclass import (
    CTWAConversionsData,
    CTWASummaryData,
)


def _to_date_str(value) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    return datetime.fromisoformat(str(value))


def _extract_rows(result) -> list[dict]:
    if not result:
        return []
    if isinstance(result, dict):
        return result.get("values") or result.get("data") or []
    if isinstance(result, list):
        return result
    return []


def _as_int(row: dict, *keys) -> int:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return int(float(value))
    return 0


def _as_float(row: dict, *keys) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return float(value)
    return 0.0


def _campaign_source(row: dict) -> str:
    return str(row.get("campaign_source") or row.get("source_id") or "")


class CTWADatalakeService:
    """
    CTWA metrics from Datalake (weni-ctwa-by-campaign).
    """

    def __init__(
        self,
        ctwa_by_campaign_client=None,
        conversations_totals_getter=None,
    ):
        self.ctwa_by_campaign_client = (
            ctwa_by_campaign_client or get_ctwa_by_campaign
        )
        self.conversations_totals_getter = (
            conversations_totals_getter or self._default_conversations_totals
        )

    def _default_conversations_totals(self, project_uuid, start_date, end_date):
        from insights.metrics.conversations.integrations.datalake.services import (
            DatalakeConversationsMetricsService,
        )

        return DatalakeConversationsMetricsService().get_conversations_totals(
            project_uuid=UUID(str(project_uuid)),
            start_date=_to_datetime(start_date),
            end_date=_to_datetime(end_date),
        )

    def _fetch_rows(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> list[dict]:
        params = {
            "project": str(project_uuid),
            "dt_start": f"{_to_date_str(start_date)} 00:00:00",
            "dt_end": f"{_to_date_str(end_date)} 23:59:59",
        }
        if campaign:
            params["campaign_source"] = str(campaign)

        result = self.ctwa_by_campaign_client(**params)
        return _extract_rows(result)

    def _aggregate_rows(self, rows: list[dict]) -> dict:
        started = sum(
            _as_int(row, "conversation_started", "conversations") for row in rows
        )
        qualified = sum(
            _as_int(row, "lead_qualified", "qualified") for row in rows
        )
        converted = sum(
            _as_int(row, "purchase_completed", "conversions") for row in rows
        )
        revenue = sum(_as_float(row, "order_value", "revenue") for row in rows)
        avg = round(revenue / converted) if converted else 0
        return {
            "started": started,
            "qualified": qualified,
            "converted": converted,
            "revenue": revenue,
            "avg": avg,
        }

    def _organic_conversations(
        self, project_uuid: str, start_date, end_date, ctwa_conversations: int
    ) -> int:
        totals = self.conversations_totals_getter(
            project_uuid=project_uuid,
            start_date=_to_datetime(start_date),
            end_date=_to_datetime(end_date),
        )
        total = getattr(
            getattr(totals, "total_conversations", None), "value", 0
        ) or 0
        return max(int(total) - ctwa_conversations, 0)

    def get_summary_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> CTWASummaryData:
        rows = self._fetch_rows(project_uuid, start_date, end_date, campaign)
        totals = self._aggregate_rows(rows)
        organic_rows = rows
        if campaign:
            organic_rows = self._fetch_rows(
                project_uuid, start_date, end_date, campaign=None
            )
        organic_ctwa = self._aggregate_rows(organic_rows)["started"]

        return CTWASummaryData(
            currency=settings.CTWA_DEFAULT_CURRENCY,
            attributed_revenue=totals["revenue"],
            avg_order_value=totals["avg"],
            ctwa_conversations=totals["started"],
            organic_conversations=self._organic_conversations(
                project_uuid, start_date, end_date, organic_ctwa
            ),
        )

    def get_conversions_data(
        self,
        project_uuid: str,
        start_date,
        end_date,
        campaign: str | None = None,
    ) -> CTWAConversionsData:
        totals = self._aggregate_rows(
            self._fetch_rows(project_uuid, start_date, end_date, campaign)
        )
        return CTWAConversionsData(
            conversations_started=totals["started"],
            conversations_qualified=totals["qualified"],
            conversations_converted=totals["converted"],
        )

    def get_performance_by_campaign(
        self,
        project_uuid: str,
        start_date,
        end_date,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        rows = self._fetch_rows(project_uuid, start_date, end_date)
        by_campaign: dict[str, dict] = {}
        for row in rows:
            source = _campaign_source(row)
            if source not in by_campaign:
                by_campaign[source] = {
                    "campaign": source,
                    "conversations": 0,
                    "qualified": 0,
                    "conversions": 0,
                    "revenue": 0.0,
                }
            by_campaign[source]["conversations"] += _as_int(
                row, "conversation_started", "conversations"
            )
            by_campaign[source]["qualified"] += _as_int(
                row, "lead_qualified", "qualified"
            )
            by_campaign[source]["conversions"] += _as_int(
                row, "purchase_completed", "conversions"
            )
            by_campaign[source]["revenue"] += _as_float(
                row, "order_value", "revenue"
            )

        ranked = sorted(
            by_campaign.values(),
            key=lambda item: item["conversations"],
            reverse=True,
        )
        page = ranked[offset : offset + limit]
        return {
            "currency": settings.CTWA_DEFAULT_CURRENCY,
            "count": len(ranked),
            "results": page,
        }
