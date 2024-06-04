import requests
from django.conf import settings


class AgentsRESTClient:
    def __init__(self, project) -> None:
        self.project = project
        self.url = f"{settings.CHATS_URL}/v1/dashboard/{self.project}/agent/"

    def headers(self, internal_token):
        return {"Authorization": f"Bearer {internal_token}"}

    def list(self, query_filters: dict):
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters.__dict__
        )
        return response.json()
