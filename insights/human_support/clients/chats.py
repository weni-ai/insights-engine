from insights.internals.base import InternalAuthentication
from django.conf import settings

import requests


class ChatsClient(InternalAuthentication):
    def __init__(self):
        self.url = settings.CHATS_URL

    def get_contacts(self, query_params: dict):
        url = f"{self.url}/v1/internal/contacts/"
        response = requests.get(
            url, headers=self.headers, params=query_params, timeout=60
        )
        response.raise_for_status()

        return response.json()
