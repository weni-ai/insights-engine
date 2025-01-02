import requests

from django.conf import settings

from insights.internals.base import InternalAuthentication


class TemplateMessagesAuthDetailsRESTClient(InternalAuthentication):
    def __init__(self, template_id: str):
        # TODO: Add the real URL when created
        self.url = f"{settings.INTEGRATIONS_URL}/api/v1/<TBD>/"

    def get_template_message_auth_details(self) -> dict:
        response = requests.get(url=self.url, headers=self.headers, timeout=60)
        data: dict = response.json()

        return {
            "access_token": data.get("access_token"),
            "whatsapp_business_account_id": data.get("whatsapp_business_account_id"),
            "name": data.get("name"),
        }
