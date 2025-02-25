from django.conf import settings
import requests
import json

from insights.internals.base import InternalAuthentication
from insights.sources.cache import CacheClient


class WeniIntegrationsClient(InternalAuthentication):
    def __init__(self, project_uuid: str):
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/apptypes/wpp-cloud/list_wpp-cloud/{project_uuid}"
        self.cache = CacheClient()
        self.cache_ttl = 300  # 5m
        self.cache_key = f"wabas:{project_uuid}"

    def get_wabas_for_project(self):
        if cached_response := self.cache.get(self.cache_key):
            return json.loads(cached_response)

        response = requests.get(url=self.url, headers=self.headers, timeout=60)
        wabas = response.json().get("data", [])

        self.cache.set(self.cache_key, json.dumps(wabas), self.cache_ttl)

        return wabas
