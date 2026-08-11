from unittest.mock import MagicMock

from django.test import SimpleTestCase
from rest_framework import status

from insights.metrics.meta.exception import (
    MetaAPIError,
    parse_meta_error_payload,
)
from insights.metrics.meta.tests.mock import (
    MOCK_ERROR_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD,
)


class TestParseMetaErrorPayload(SimpleTestCase):
    def test_parses_graph_api_error_object(self):
        response = MagicMock()
        response.json.return_value = MOCK_ERROR_RESPONSE_BODY

        payload = parse_meta_error_payload(response)

        self.assertEqual(payload["code"], 100)
        self.assertEqual(payload["error_subcode"], 33)
        self.assertEqual(payload["type"], "GraphMethodException")
        self.assertEqual(
            payload["fbtrace_id"],
            MOCK_ERROR_RESPONSE_BODY["error"]["fbtrace_id"],
        )

    def test_parses_invalid_period_error_fields(self):
        response = MagicMock()
        response.json.return_value = MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD

        payload = parse_meta_error_payload(response)

        meta = MOCK_TEMPLATE_DAILY_ANALYTICS_INVALID_PERIOD["error"]
        self.assertEqual(payload["code"], meta["code"])
        self.assertEqual(payload["error_subcode"], meta["error_subcode"])
        self.assertEqual(payload["error_user_msg"], meta["error_user_msg"])
        self.assertEqual(payload["is_transient"], meta["is_transient"])

    def test_falls_back_when_body_is_not_json(self):
        response = MagicMock()
        response.json.side_effect = ValueError("not json")
        response.text = "plain text error"

        payload = parse_meta_error_payload(response)

        self.assertEqual(payload, {"message": "plain text error"})

    def test_falls_back_when_response_is_none(self):
        payload = parse_meta_error_payload(None)
        self.assertEqual(payload, {"message": "Unknown Meta API error"})


class TestMetaAPIError(SimpleTestCase):
    def test_preserves_numeric_meta_fields_in_detail(self):
        meta_error = {
            "message": "Invalid parameter",
            "type": "OAuthException",
            "code": 100,
            "error_subcode": 4182001,
            "fbtrace_id": "trace123",
            "is_transient": False,
        }

        error = MetaAPIError(meta_error=meta_error, event_id="sentry-id")

        self.assertEqual(error.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(error.detail["error"]["code"], "meta_api_error")
        self.assertEqual(error.detail["error"]["message"], "Invalid parameter")
        self.assertEqual(error.detail["error"]["event_id"], "sentry-id")
        self.assertIsInstance(error.detail["error"]["meta"]["code"], int)
        self.assertEqual(error.detail["error"]["meta"]["code"], 100)
        self.assertEqual(error.detail["error"]["meta"]["error_subcode"], 4182001)
        self.assertIs(error.detail["error"]["meta"]["is_transient"], False)
