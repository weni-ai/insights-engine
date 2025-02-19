import json
import requests

from datetime import date
from django.conf import settings
from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.enums import (
    AnalyticsGranularity,
    MetricsTypes,
)
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.utils import convert_date_to_unix_timestamp
from insights.sources.cache import CacheClient


class MetaAPIClient:
    base_host_url = "https://graph.facebook.com"
    access_token = settings.WHATSAPP_API_ACCESS_TOKEN

    def __init__(self):
        self.cache = CacheClient()
        self.cache_ttl = 3600  # 1h

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_templates_list(self, waba_id: str):
        url = f"{self.base_host_url}/v21.0/{waba_id}/message_templates"

        params = {
            "limit": 9999,
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

        return response.json()

    def get_template_preview_cache_key(self, template_id: str) -> str:
        return f"meta_template_preview:{template_id}"

    def get_template_preview(self, template_id: str):
        cache_key = self.get_template_preview_cache_key(template_id=template_id)

        if cached_response := self.cache.get(cache_key):
            return json.loads(cached_response)

        url = f"{self.base_host_url}/v21.0/{template_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"Error ({err.response.status_code}): {err.response.text}")

            raise ValidationError(
                {"error": "An error has occurred"}, code="meta_api_error"
            ) from err

        response = response.json()
        self.cache.set(cache_key, json.dumps(response, default=str), self.cache_ttl)

        return response

    def get_analytics_cache_key(
        self, waba_id: str, template_id: str, params: dict
    ) -> str:
        return f"meta_msgs_analytics:{waba_id}:{template_id}:{json.dumps(params, sort_keys=True)}"

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

        cache_key = self.get_analytics_cache_key(
            waba_id=waba_id, template_id=template_id, params=params
        )

        if cached_response := self.cache.get(cache_key):
            return json.loads(cached_response)

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
        response = {"data": format_messages_metrics_data(meta_response.get("data")[0])}

        self.cache.set(cache_key, json.dumps(response, default=str), self.cache_ttl)

        return response

    def get_button_analytics_cache_key(
        self, waba_id: str, template_id: str, params: dict
    ) -> str:
        return f"meta_button_analytics:{waba_id}:{template_id}:{json.dumps(params, sort_keys=True)}"

    def get_buttons_analytics(
        self,
        waba_id: str,
        template_id: str,
        start_date: date,
        end_date: date,
    ):
        metrics_types = [
            MetricsTypes.SENT.value,
            MetricsTypes.CLICKED.value,
        ]

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": convert_date_to_unix_timestamp(start_date),
            "end": convert_date_to_unix_timestamp(end_date),
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
        }

        cache_key = self.get_button_analytics_cache_key(
            waba_id=waba_id, template_id=template_id, params=params
        )

        if cached_response := self.cache.get(cache_key):
            return json.loads(cached_response)

        template_data: dict = self.get_template_preview(template_id=template_id)
        components = template_data.get("components", [])

        buttons = []

        for component in components:
            if component.get("type", "") == "BUTTONS":
                buttons = component.get("buttons", [])
                break

        if buttons == []:
            return {"data": []}

        url = f"{self.base_host_url}/v21.0/{waba_id}/template_analytics?"

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
        data_points = meta_response.get("data", {})[0].get("data_points", [])
        response = {"data": format_button_metrics_data(buttons, data_points)}

        self.cache.set(cache_key, json.dumps(response, default=str), self.cache_ttl)

        return response
