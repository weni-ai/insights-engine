import json
import responses

from django.test import TestCase
from rest_framework import status

from insights.sources.meta_message_templates.clients import MetaAPIClient


class TestMetaAPIClient(TestCase):
    def setUp(self):
        self.base_host_url = "https://graph.facebook.com"

    def test_get_template_preview(self):
        client = MetaAPIClient()

        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{template_id}"

        mocked_success_response_body = {
            "name": "testing",
            "parameter_format": "POSITIONAL",
            "components": [
                {"type": "HEADER", "format": "TEXT", "text": "Test"},
                {"type": "BODY", "text": "Just testing"},
            ],
            "language": "en_US",
            "status": "APPROVED",
            "category": "MARKETING",
            "id": template_id,
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(mocked_success_response_body),
            )

            preview_response = client.get_template_preview(template_id=template_id)
            self.assertEqual(preview_response, mocked_success_response_body)
