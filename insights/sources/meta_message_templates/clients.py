import requests

from django.conf import settings
from rest_framework.exceptions import ValidationError


class MetaAPIClient:
    base_host_url = "https://graph.facebook.com"
    access_token = settings.WHATSAPP_API_ACCESS_TOKEN

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_template_preview(self, template_id: str):
        url = f"{self.base_host_url}/v21.0/{template_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"Error ({err.response.status_code}): {err.response.text}")

            raise ValidationError(
                {"error": "An error has occurred"}, code="meta_api_error"
            ) from err

        return response.json()
