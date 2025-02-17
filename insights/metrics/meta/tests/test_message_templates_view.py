import json
import responses

from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.sources.meta_message_templates.validators import ANALYTICS_REQUIRED_FIELDS
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
)


class BaseTestMetaMessageTemplatesView(APITestCase):
    def get_preview(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/preview/"

        return self.client.get(url, query_params)

    def get_messages_analytics(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/messages-analytics/"

        return self.client.get(url, query_params)

    def get_buttons_analytics(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/buttons-analytics/"

        return self.client.get(url, query_params)


class TestMetaMessageTemplatesView(BaseTestMetaMessageTemplatesView):
    def setUp(self):
        self.meta_api_client: MetaAPIClient = MetaAPIClient()

        return super().setUp()

    def test_get_preview(self):
        template_id = "1234567890987654"

        url = f"{self.meta_api_client.base_host_url}/v21.0/{template_id}"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )

            response = self.get_preview({"template_id": template_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MOCK_SUCCESS_RESPONSE_BODY)

    def test_cannot_get_preview_missing_template_id(self):
        response = self.get_preview({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "template_id_missing")

    def test_get_messages_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"

        url = f"{self.meta_api_client.base_host_url}/v21.0/{waba_id}/template_analytics"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            response = self.get_messages_analytics(
                {
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                }
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = {
            "data": format_messages_metrics_data(
                MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
            )
        }

        self.assertEqual(response.data, expected_response)

    def test_cannot_get_messages_analytics_missing_required_params(self):
        response = self.get_messages_analytics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "required_fields_missing")
        self.assertEqual(
            response.data,
            {
                "error": f"Required fields are missing: {', '.join(ANALYTICS_REQUIRED_FIELDS)}"
            },
        )

    def test_get_buttons_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{self.meta_api_client.base_host_url}/v21.0/{template_id}",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )
            rsps.add(
                responses.GET,
                f"{self.meta_api_client.base_host_url}/v21.0/{waba_id}/template_analytics",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            response = self.get_buttons_analytics(
                {
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                }
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for component in MOCK_SUCCESS_RESPONSE_BODY["components"]:
            if component.get("type", "") == "BUTTONS":
                buttons = component.get("buttons", [])
                break

        expected_response = {
            "data": format_button_metrics_data(
                buttons,
                MOCK_TEMPLATE_DAILY_ANALYTICS.get("data", {})[0].get("data_points", []),
            )
        }

        self.assertEqual(response.data, expected_response)

    def test_cannot_get_buttons_analytics_missing_required_params(self):
        response = self.get_buttons_analytics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "required_fields_missing")
        self.assertEqual(
            response.data,
            {
                "error": f"Required fields are missing: {', '.join(ANALYTICS_REQUIRED_FIELDS)}"
            },
        )
