import json
import responses

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.exceptions import ValidationError

from insights.projects.parsers import parse_dict_to_json
from insights.sources.meta_message_templates.enums import (
    Operations,
)
from insights.sources.meta_message_templates.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.sources.meta_message_templates.enums import Operations
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
    MOCK_TEMPLATES_LIST_BODY,
)
from insights.sources.meta_message_templates.usecases.query_execute import QueryExecutor


class TestMessageTemplateQueryExecutor(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_list_templates_operation(self):
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

            result = QueryExecutor.execute(
                filters={"waba_id": waba_id},
                operation=Operations.LIST_TEMPLATES.value,
                parser=parse_dict_to_json,
            )

            self.assertEqual(result, MOCK_TEMPLATES_LIST_BODY)

    def test_cannot_list_templates_when_missing_waba_id(self):
        with self.assertRaises(ValidationError) as context:
            QueryExecutor.execute(
                filters={},
                operation=Operations.LIST_TEMPLATES.value,
                parser=parse_dict_to_json,
            )
            self.assertEqual(context.exception.code, "waba_id_missing")

    def test_template_preview_operation(self):
        template_id = "1234567890987654"
        url = f"https://graph.facebook.com/v21.0/{template_id}"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_SUCCESS_RESPONSE_BODY),
            )

            result = QueryExecutor.execute(
                filters={"template_id": template_id},
                operation=Operations.TEMPLATE_PREVIEW.value,
                parser=parse_dict_to_json,
            )
            self.assertEqual(result, MOCK_SUCCESS_RESPONSE_BODY)

    def test_cannot_get_template_preview_without_including_id_in_the_filters(self):
        with self.assertRaises(ValidationError) as context:
            QueryExecutor.execute(
                filters={},
                operation=Operations.TEMPLATE_PREVIEW.value,
                parser=parse_dict_to_json,
            )

            self.assertEqual(context.exception.code, "template_id_missing")

    def test_cannot_perform_unsupported_operation(self):
        with self.assertRaises(ValidationError) as context:
            QueryExecutor.execute(
                filters={},
                operation="example",
                parser=parse_dict_to_json,
            )

            self.assertEqual(context.exception.code, "unsupported_operation")

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

            result = QueryExecutor.execute(
                filters={
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                },
                operation=Operations.MESSAGES_ANALYTICS.value,
                parser=parse_dict_to_json,
            )
            expected_response = {
                "data": format_messages_metrics_data(
                    MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
                )
            }

            self.assertEqual(result, expected_response)

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

            result = QueryExecutor.execute(
                filters={
                    "waba_id": waba_id,
                    "template_id": template_id,
                    "start_date": str(timezone.now().date() - timedelta(days=7)),
                    "end_date": str(timezone.now().date()),
                },
                operation=Operations.BUTTONS_ANALYTICS.value,
                parser=parse_dict_to_json,
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
