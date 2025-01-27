import json
import responses

from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_ERROR_RESPONSE_BODY,
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
    MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD,
)
from insights.utils import convert_date_str_to_datetime_date


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

            with self.assertRaises(ValidationError) as context:
                client.get_template_preview(template_id=template_id)
                self.assertEqual(context.exception.code, "meta_api_error")

    def test_get_template_daily_analytics(self):
        client = MetaAPIClient()

        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/0000000000000000/template_analytics"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            start_date = convert_date_str_to_datetime_date("2024-12-01")
            end_date = convert_date_str_to_datetime_date("2024-12-31")

            preview_response = client.get_messages_analytics(
                waba_id=waba_id,
                template_id=template_id,
                start_date=start_date,
                end_date=end_date,
            )

            expected_response = {
                "data": format_messages_metrics_data(
                    MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
                )
            }

            self.assertEqual(preview_response, expected_response)

    def test_cannot_get_template_daily_analytics_when_an_error_has_occurred(self):
        client = MetaAPIClient()

        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/0000000000000000/template_analytics"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD),
            )

            start_date = convert_date_str_to_datetime_date("2022-01-01")
            end_date = convert_date_str_to_datetime_date("2024-12-31")

            with self.assertRaises(ValidationError) as context:
                client.get_messages_analytics(
                    waba_id=waba_id,
                    template_id=template_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                self.assertEqual(context.exception.code, "meta_api_error")

    def test_get_template_buttons_analytics(self):
        client = MetaAPIClient()

        waba_id = "0000000000000000"
        template_id = "1234567890987654"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{self.base_host_url}/v21.0/{template_id}",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )
            rsps.add(
                responses.GET,
                f"{self.base_host_url}/v21.0/0000000000000000/template_analytics",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            start_date = convert_date_str_to_datetime_date("2024-12-01")
            end_date = convert_date_str_to_datetime_date("2024-12-31")

            preview_response = client.get_buttons_analytics(
                waba_id=waba_id,
                template_id=template_id,
                start_date=start_date,
                end_date=end_date,
            )

            buttons = []

            for component in MOCK_SUCCESS_RESPONSE_BODY["components"]:
                if component.get("type", "") == "BUTTONS":
                    buttons = component.get("buttons", [])
                    break

            expected_response = {
                "data": format_button_metrics_data(
                    buttons,
                    MOCK_TEMPLATE_DAILY_ANALYTICS.get("data", {})[0].get(
                        "data_points", []
                    ),
                )
            }

            self.assertEqual(preview_response, expected_response)
