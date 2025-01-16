import requests

from datetime import date
from django.conf import settings
from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.enums import (
    AnalyticsGranularity,
    MetricsTypes,
)
from insights.sources.meta_message_templates.utils import (
    format_messages_metrics_data,
    format_messages_metrics_data_points,
)
from insights.utils import convert_date_to_unix_timestamp


class MetaAPIClient:
    base_host_url = "https://graph.facebook.com"
    access_token = settings.WHATSAPP_API_ACCESS_TOKEN

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_template_preview(self, template_id: str):
        url = f"{self.base_host_url}/v21.0/{template_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"Error ({err.response.status_code}): {err.response.text}")

            raise ValidationError(
                {"error": "An error has occurred"}, code="meta_api_error"
            ) from err

        return response.json()

    def get_messages_analytics(
        self,
        waba_id: str,
        template_id: str,
        start_date: date,
        end_date: date,
    ):
        url = f"{self.base_host_url}/v21.0/{waba_id}/template_analytics?"

        metrics_types = [
            MetricsTypes.SENT.value,
            MetricsTypes.DELIVERED.value,
            MetricsTypes.READ.value,
            MetricsTypes.CLICKED.value,
        ]

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": convert_date_to_unix_timestamp(start_date),
            "end": convert_date_to_unix_timestamp(end_date),
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
        }

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=60
            )
            response.raise_for_status()

        except requests.HTTPError as err:
            print(f"Error ({err.response.status_code}): {err.response.text}")

            raise ValidationError(
                {"error": "An error has occurred"}, code="meta_api_error"
            ) from err

        meta_response = response.json()

        return {"data": format_messages_metrics_data(meta_response.get("data")[0])}
