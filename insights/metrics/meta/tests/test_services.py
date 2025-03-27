import json
import responses

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.exceptions import ValidationError

from insights.metrics.meta.services import MetaMessageTemplatesService
from insights.metrics.meta.tests.mock import (
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
    MOCK_TEMPLATES_LIST_BODY,
)
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)


class TestMetaMessageTemplatesService(TestCase):
    def setUp(self):
        self.service = MetaMessageTemplatesService()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_get_templates_list(self):
        waba_id = "12345678"
        url = f"https://graph.facebook.com/v21.0/{waba_id}/message_templates"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATES_LIST_BODY),
            )

            result = self.service.get_templates_list(filters={"waba_id": waba_id})

            self.assertEqual(result, MOCK_TEMPLATES_LIST_BODY)

    def test_cannot_get_templates_list_when_missing_waba_id(self):
        with self.assertRaises(ValidationError) as context:
            self.service.get_templates_list(filters={})

        self.assertEqual(context.exception.detail["error"].code, "waba_id_missing")

    def test_get_template_preview(self):
        template_id = "12345678"
        url = f"https://graph.facebook.com/v21.0/{template_id}"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )

            result = self.service.get_template_preview(
                filters={"template_id": template_id}
            )

            self.assertEqual(result, MOCK_SUCCESS_RESPONSE_BODY)

    def test_cannot_get_template_preview_without_including_id_in_the_filters(self):
        with self.assertRaises(ValidationError) as context:
            self.service.get_template_preview(filters={})

        self.assertEqual(context.exception.detail["error"].code, "template_id_missing")

    def test_get_template_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        url = f"https://graph.facebook.com/v21.0/{waba_id}/template_analytics"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            result = self.service.get_messages_analytics(
                filters={
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                }
            )

            expected_response = {
                "data": format_messages_metrics_data(
                    MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
                )
            }

            self.assertEqual(result, expected_response)

    def test_cannot_get_template_analytics_when_missing_required_fields(self):
        with self.assertRaises(ValidationError) as context:
            self.service.get_messages_analytics(filters={})

        self.assertEqual(
            context.exception.detail["error"].code, "required_fields_missing"
        )

    def test_get_template_buttons_analytics(self):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"https://graph.facebook.com/v21.0/{template_id}",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )
            rsps.add(
                responses.GET,
                f"https://graph.facebook.com/v21.0/{waba_id}/template_analytics",
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_TEMPLATE_DAILY_ANALYTICS),
            )

            result = self.service.get_buttons_analytics(
                filters={
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                }
            )

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

            self.assertEqual(result, expected_response)
