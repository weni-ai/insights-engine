from dataclasses import dataclass
from datetime import date

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.enums import ProductType
from django.conf import settings


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

    def execute(
        self,
        waba_templates: list[WabaTemplateIDs],
        start_date: date,
        end_date: date,
    ) -> dict:
        data_points: list[dict] = []

        for group in waba_templates:
            for product_type in (
                ProductType.CLOUD_API.value,
                ProductType.MM_LITE.value,
            ):
                data_points.extend(
                    self._fetch_analytics_in_chunks(
                        waba_id=group.waba_id,
                        template_ids=group.template_ids,
                        start_date=start_date,
                        end_date=end_date,
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
