import json
import responses

from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.enums import (
    AnalyticsGranularity,
    MetricsTypes,
)
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_ERROR_RESPONSE_BODY,
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
    MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD,
    MOCK_TEMPLATES_LIST_BODY,
)
from insights.utils import (
    convert_date_str_to_datetime_date,
    convert_date_to_unix_timestamp,
)


class TestMetaAPIClient(TestCase):
    def setUp(self):
        self.base_host_url = "https://graph.facebook.com"
        self.client: MetaAPIClient = MetaAPIClient()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_list_templates(self):
        waba_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{waba_id}/message_templates"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATES_LIST_BODY),
            )

            response_data = self.client.get_templates_list(waba_id=waba_id)
            self.assertEqual(response_data, MOCK_TEMPLATES_LIST_BODY)
            self.assertEqual(len(rsps.calls), 1)

    def test_get_template_preview(self):
        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/{template_id}"

        cache_key = self.client.get_template_preview_cache_key(template_id=template_id)

        self.assertIsNone(self.client.cache.get(cache_key))

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )

            preview_response = self.client.get_template_preview(template_id=template_id)
            self.assertEqual(preview_response, MOCK_SUCCESS_RESPONSE_BODY)

            self.assertEqual(len(rsps.calls), 1)  # URL called once

            cached_response = self.client.cache.get(cache_key)
            self.assertIsNotNone(cached_response)

            self.assertEqual(json.loads(cached_response), MOCK_SUCCESS_RESPONSE_BODY)

            # URL should not be called again due to cache
            self.client.get_template_preview(template_id=template_id)
            self.assertEqual(len(rsps.calls), 1)  # number of calls has not changed

    def test_cannot_get_template_preview_when_template_does_not_exist(self):
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
                self.client.get_template_preview(template_id=template_id)
                self.assertEqual(context.exception.code, "meta_api_error")

    def test_get_template_daily_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        url = f"{self.base_host_url}/v21.0/0000000000000000/template_analytics"

        metrics_types = [
            MetricsTypes.SENT.value,
            MetricsTypes.DELIVERED.value,
            MetricsTypes.READ.value,
            MetricsTypes.CLICKED.value,
        ]

        start_date = convert_date_str_to_datetime_date("2024-12-01")
        end_date = convert_date_str_to_datetime_date("2024-12-31")

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": convert_date_to_unix_timestamp(start_date),
            "end": convert_date_to_unix_timestamp(end_date),
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
            "limit": 9999,
        }

        cache_key = self.client.get_analytics_cache_key(
            waba_id=waba_id, template_id=template_id, params=params
        )

        self.assertIsNone(self.client.cache.get(cache_key))

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            response = self.client.get_messages_analytics(
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

            self.assertEqual(response, expected_response)

            self.assertEqual(len(rsps.calls), 1)  # URL called once

            cached_response = self.client.cache.get(cache_key)
            self.assertIsNotNone(cached_response)

            self.assertEqual(expected_response, json.loads(cached_response))

            # URL should not called again due to cached response
            self.client.get_messages_analytics(
                waba_id=waba_id,
                template_id=template_id,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertEqual(len(rsps.calls), 1)

    def test_cannot_get_template_daily_analytics_when_an_error_has_occurred(self):
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
                self.client.get_messages_analytics(
                    waba_id=waba_id,
                    template_id=template_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                self.assertEqual(context.exception.code, "meta_api_error")

    def test_get_template_buttons_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"

        start_date = convert_date_str_to_datetime_date("2024-12-01")
        end_date = convert_date_str_to_datetime_date("2024-12-31")

        metrics_types = [
            MetricsTypes.SENT.value,
            MetricsTypes.CLICKED.value,
        ]

        params = {
            "granularity": AnalyticsGranularity.DAILY.value,
            "start": convert_date_to_unix_timestamp(start_date),
            "end": convert_date_to_unix_timestamp(end_date),
            "metric_types": ",".join(metrics_types),
            "template_ids": template_id,
            "limit": 9999,
        }

        cache_key = self.client.get_button_analytics_cache_key(
            waba_id=waba_id, template_id=template_id, params=params
        )

        self.assertIsNone(self.client.cache.get(cache_key))

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

            preview_response = self.client.get_buttons_analytics(
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

            self.assertEqual(len(rsps.calls), 2)  # each URL called once

            cached_response = self.client.cache.get(cache_key)
            self.assertIsNotNone(cached_response)

            self.assertEqual(expected_response, json.loads(cached_response))

            # URLs should not called again due to cached response
            self.client.get_buttons_analytics(
                waba_id=waba_id,
                template_id=template_id,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertEqual(len(rsps.calls), 2)
