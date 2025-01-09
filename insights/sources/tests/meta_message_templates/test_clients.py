import json
import requests
import responses

from django.test import TestCase
from rest_framework import status

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_ERROR_RESPONSE_BODY,
    MOCK_SUCCESS_RESPONSE_BODY,
)


class TestMetaAPIClient(TestCase):
    def setUp(self):
        self.base_host_url = "https://graph.facebook.com"

    def test_get_template_preview(self):
        client = MetaAPIClient()

        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{template_id}"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )

            preview_response = client.get_template_preview(template_id=template_id)
            self.assertEqual(preview_response, MOCK_SUCCESS_RESPONSE_BODY)

    def test_cannot_get_template_preview_when_template_does_not_exist(self):
        client = MetaAPIClient()

        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{template_id}"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
                body=json.dumps(MOCK_ERROR_RESPONSE_BODY),
            )

            with self.assertRaises(requests.exceptions.HTTPError):
                client.get_template_preview(template_id=template_id)
