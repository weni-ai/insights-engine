import json
import logging
import requests

from datetime import date, datetime

from django.conf import settings
from rest_framework.exceptions import ValidationError, NotFound

from insights.metrics.meta.enums import AnalyticsGranularity, MetricsTypes
from insights.metrics.meta.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.utils import convert_date_to_unix_timestamp
from insights.sources.cache import CacheClient


logger = logging.getLogger(__name__)


class MetaGraphAPIClient:
    base_host_url = "https://graph.facebook.com/v21.0"
    access_token = settings.WHATSAPP_API_ACCESS_TOKEN

    def __init__(self):
        self.cache = CacheClient()
        self.cache_ttl = 3600  # 1h

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_templates_list(
        self,
        waba_id: str,
        name: str | None = None,
        limit: int = 9999,
        fields: list[str] | None = None,
        before: str | None = None,
        after: str | None = None,
        language: str | None = None,
        category: str | None = None,
    ):
        url = f"{self.base_host_url}/{waba_id}/message_templates"

        params = {
            filter_name: filter_value
            for filter_name, filter_value in {
                "name": name,
                "limit": limit,
                "fields": ",".join(fields) if fields else None,
                "language": language,
                "category": category,
            }.items()
            if filter_value is not None
        }

        if before:
            params["before"] = before

        elif after:
            params["after"] = after

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=60
            )
            response.raise_for_status()
        except requests.HTTPError as err:
            logger.error(
                "Error getting templates list: %s. Original exception: %s",
                err.response.text,
                err,
                exc_info=True,
            )

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

        url = f"{self.base_host_url}/{template_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as err:
            logger.error(
                "Error getting template preview: %s. Original exception: %s",
                err.response.text,
                err,
                exc_info=True,
            )

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
        template_id: str | list[str],
        start_date: date,
        end_date: date,
    ):
        url = f"{self.base_host_url}/{waba_id}/template_analytics?"

        metrics_types = [
            MetricsTypes.SENT.value,
            MetricsTypes.DELIVERED.value,
            MetricsTypes.READ.value,
            MetricsTypes.CLICKED.value,
        ]

        if isinstance(template_id, list):
            template_id = ",".join(template_id)

        start = convert_date_to_unix_timestamp(start_date)
        end = convert_date_to_unix_timestamp(end_date, use_max_time=True)

        now = int(datetime.now().timestamp())

        if end > now:
            end = now

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": start,
            "end": end,
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
            "limit": 9999,
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
            logger.error(
                "Error getting messages analytics: %s. Original exception: %s",
                err.response.text,
                err,
                exc_info=True,
            )

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

        start = convert_date_to_unix_timestamp(start_date)
        end = convert_date_to_unix_timestamp(end_date, use_max_time=True)

        now = int(datetime.now().timestamp())

        if end > now:
            end = now

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": start,
            "end": end,
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
            "limit": 9999,
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

        url = f"{self.base_host_url}/{waba_id}/template_analytics?"

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=60
            )
            response.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 404:
                raise NotFound(
                    {"error": "Template not found"}, code="template_not_found"
                ) from err

            logger.error(
                "Error getting buttons analytics: %s. Original exception: %s",
                err.response.text,
                err,
                exc_info=True,
            )

            raise ValidationError(
                {"error": "An error has occurred"}, code="meta_api_error"
            ) from err

        meta_response = response.json()
        data_points = meta_response.get("data", {})[0].get("data_points", [])
        response = {"data": format_button_metrics_data(buttons, data_points)}

        self.cache.set(cache_key, json.dumps(response, default=str), self.cache_ttl)

        return response
