import json
import responses

from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from insights.projects.parsers import parse_dict_to_json
from insights.sources.meta_message_templates.enums import Operations
from insights.sources.tests.meta_message_templates.mock import (
    MOCK_SUCCESS_RESPONSE_BODY,
)
from insights.sources.meta_message_templates.usecases.query_execute import QueryExecutor


class TestMessageTemplateQueryExecutor(TestCase):
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
