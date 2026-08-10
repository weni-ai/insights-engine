import logging
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.enums import ProductType
from insights.metrics.meta.usecases.waba_migration_analytics import (
    WabaAnalyticsPeriod,
    resolve_old_template_id,
    resolve_waba_analytics_periods,
)

logger = logging.getLogger(__name__)

EMPTY_TEMPLATE_METRICS = {
    "sent": 0,
    "delivered": 0,
    "read": 0,
    "clicked": 0,
}


@dataclass
class WabaTemplateIDs:
    waba_id: str
    template_ids: list[str]


class GetTemplatesMetricsFromMultipleWabasUseCase:
    def __init__(self, meta_client: MetaGraphAPIClient | None = None):
        self.meta_client = meta_client or MetaGraphAPIClient()

    def _fetch_analytics_in_chunks(
        self,
        waba_id: str,
        template_ids: list[str],
        start_date: date,
        end_date: date,
        product_type: str,
    ) -> list[dict]:
        data_points = []
        chunk_size = settings.WHATSAPP_TEMPLATE_IDS_PER_REQUEST
        for i in range(0, len(template_ids), chunk_size):
            chunk = template_ids[i : i + chunk_size]
            metrics = self.meta_client.get_messages_analytics(
                waba_id=waba_id,
                template_id=chunk,
                start_date=start_date,
                end_date=end_date,
                product_type=product_type,
            )
            data_points.extend(metrics.get("data", {}).get("data_points", []))
        return data_points

    def _template_ids_for_period(
        self,
        *,
        current_waba_id: str,
        period: WabaAnalyticsPeriod,
        new_template_ids: list[str],
    ) -> list[str]:
        if period.waba_id == current_waba_id:
            return new_template_ids

        old_template_ids: list[str] = []
        for new_template_id in new_template_ids:
            try:
                old_template_id = resolve_old_template_id(
                    self.meta_client,
                    old_waba_id=period.waba_id,
                    new_template_id=new_template_id,
                )
            except Exception as error:
                capture_exception(error)
                logger.warning(
                    "Failed to resolve old template id for new_template_id=%s "
                    "on old_waba_id=%s; skipping this template. Error: %s",
                    new_template_id,
                    period.waba_id,
                    error,
                    exc_info=True,
                )
                continue

            if old_template_id:
                old_template_ids.append(old_template_id)

        # Same template name across languages can resolve to the same old ID.
        return list(dict.fromkeys(old_template_ids))

    def _fetch_period_data_points(
        self,
        *,
        current_waba_id: str,
        period: WabaAnalyticsPeriod,
        template_ids: list[str],
    ) -> list[dict]:
        is_old_waba = period.waba_id != current_waba_id
        data_points: list[dict] = []

        for product_type in (
            ProductType.CLOUD_API.value,
            ProductType.MM_LITE.value,
        ):
            try:
                data_points.extend(
                    self._fetch_analytics_in_chunks(
                        waba_id=period.waba_id,
                        template_ids=template_ids,
                        start_date=period.start_date,
                        end_date=period.end_date,
                        product_type=product_type,
                    )
                )
            except Exception as error:
                if not is_old_waba:
                    raise

                capture_exception(error)
                logger.warning(
                    "Failed to fetch analytics for old_waba_id=%s "
                    "product_type=%s; skipping this period/product. Error: %s",
                    period.waba_id,
                    product_type,
                    error,
                    exc_info=True,
                )

        return data_points

    def execute(
        self,
        waba_templates: list[WabaTemplateIDs],
        start_date: date,
        end_date: date,
    ) -> dict:
        data_points: list[dict] = []

        for group in waba_templates:
            periods = resolve_waba_analytics_periods(
                current_waba_id=group.waba_id,
                start_date=start_date,
                end_date=end_date,
            )

            for period in periods:
                template_ids = self._template_ids_for_period(
                    current_waba_id=group.waba_id,
                    period=period,
                    new_template_ids=group.template_ids,
                )
                if not template_ids:
                    continue

                data_points.extend(
                    self._fetch_period_data_points(
                        current_waba_id=group.waba_id,
                        period=period,
                        template_ids=template_ids,
                    )
                )

        result = dict(EMPTY_TEMPLATE_METRICS)

        for day_data in data_points:
            result["sent"] += day_data["sent"]
            result["delivered"] += day_data["delivered"]
            result["read"] += day_data["read"]
            result["clicked"] += day_data["clicked"]

        return result
