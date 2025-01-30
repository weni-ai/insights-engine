import requests
from django.conf import settings


class UpdateContactName:
    def __init__(self, api_token):
        self.headers = {
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": f"Token {api_token}",
        }

    def get_contact_name(self, contact_uuid):
        response = requests.get(
            headers=self.headers,
            url=f"{settings.FLOWS_URL}/api/v2/contacts.json?uuid={contact_uuid}",
        )
        response_data = response.json()

        name = (
            response_data["results"][0]["name"] if response_data.get("results") else ""
        )

        return name
