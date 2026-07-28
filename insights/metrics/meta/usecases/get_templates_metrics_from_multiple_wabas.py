from dataclasses import dataclass
from datetime import date

from django.conf import settings

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.enums import ProductType
from insights.metrics.meta.usecases.waba_migration_analytics import (
    WabaAnalyticsPeriod,
    resolve_old_template_id,
    resolve_waba_analytics_periods,
)


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
            old_template_id = resolve_old_template_id(
                self.meta_client,
                old_waba_id=period.waba_id,
                new_template_id=new_template_id,
            )
            if old_template_id:
                old_template_ids.append(old_template_id)

        return old_template_ids

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

                for product_type in (
                    ProductType.CLOUD_API.value,
                    ProductType.MM_LITE.value,
                ):
                    data_points.extend(
                        self._fetch_analytics_in_chunks(
                            waba_id=period.waba_id,
                            template_ids=template_ids,
                            start_date=period.start_date,
                            end_date=period.end_date,
                            product_type=product_type,
                        )
                    )

        result = {
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "clicked": 0,
        }

        for day_data in data_points:
            result["sent"] += day_data["sent"]
            result["delivered"] += day_data["delivered"]
            result["read"] += day_data["read"]
            result["clicked"] += day_data["clicked"]

        return result
