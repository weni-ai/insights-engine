import requests
from django.conf import settings


class Connection:
    def __init__(self, endpoint: str) -> None:
        self.base_url = settings.FLOWS_ES_DATABASE + endpoint

    def get(self, params: dict):
        return requests.get(url=self.base_url, params=params).json()
