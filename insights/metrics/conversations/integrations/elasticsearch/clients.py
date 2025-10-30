import requests

from django.conf import settings


class ElasticsearchClient:
    def __init__(self):
        self.base_url = settings.FLOWS_ES_DATABASE

    def get(self, endpoint: str, params: dict, query: dict):
        return requests.get(
            url=f"{self.base_url}/{endpoint}", params=params, json=query
        ).json()
