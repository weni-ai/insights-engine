import json
import pdb
import requests
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
                {"type": "HEADER", "format": "TEXT", "text": "ATENÇÃO AO PRAZO!"},
                {
                    "type": "BODY",
                    "text": "Just testing",
                    "example": {"body_text": [["test"]]},
                },
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {"type": "URL", "text": "link", "url": "https://example.local/"}
                    ],
                },
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

    def test_cannot_get_template_preview_when_template_does_not_exist(self):
        client = MetaAPIClient()

        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{template_id}"

        mocked_error_response_body = {
            "error": {
                "message": "Unsupported get request. Object with ID '1234567890987654' does not exist, cannot be loaded due to missing permissions, or does not support this operation. Please read the Graph API documentation at https://developers.facebook.com/docs/graph-api",
                "type": "GraphMethodException",
                "code": 100,
                "error_subcode": 33,
                "fbtrace_id": "fjXJSSiOahsAHSshASQEOEQ",
            }
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
                body=json.dumps(mocked_error_response_body),
            )

            with self.assertRaises(requests.exceptions.HTTPError):
                client.get_template_preview(template_id=template_id)
