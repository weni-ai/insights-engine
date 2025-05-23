import logging
import requests
import json

from django.conf import settings
from rest_framework import status
from sentry_sdk import capture_message
from insights.internals.base import InternalAuthentication
from insights.sources.cache import CacheClient


logger = logging.getLogger(__name__)


class WeniIntegrationsClient(InternalAuthentication):
    def __init__(self):
        self.base_url = f"{settings.INTEGRATIONS_URL}"
        self.cache = CacheClient()

    def get_wabas_for_project(self, project_uuid: str):
        url = f"{self.base_url}/api/v1/apptypes/wpp-cloud/list_wpp-cloud/{project_uuid}"
        cache_key = f"wabas:{project_uuid}"
        cache_ttl = 60  # 1m

        if cached_response := self.cache.get(cache_key):
            return json.loads(cached_response)

        response = requests.get(url=url, headers=self.headers, timeout=60)

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching wabas for project %s: %s - %s",
                project_uuid,
                response.status_code,
                response.text,
            )
            capture_message(response.text)

            raise ValueError(response.text)

        wabas = response.json().get("data", [])

        self.cache.set(cache_key, json.dumps(wabas), cache_ttl)

        return wabas

    def get_template_data_by_id(self, project_uuid: str, template_id: str):
        url = f"{self.base_url}/api/v1/project/templates/details/"

        response = requests.get(
            url=url,
            headers=self.headers,
            timeout=60,
            params={"project_uuid": project_uuid, "template_id": template_id},
        )

        return response
