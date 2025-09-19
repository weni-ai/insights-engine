import requests

from django.conf import settings


class ElasticsearchClient:
    def __init__(self):
        self.base_url = settings.FLOWS_ES_DATABASE

    def get(self, params: dict, query: dict):
        return requests.get(url=self.base_url, params=params, json=query).json()
