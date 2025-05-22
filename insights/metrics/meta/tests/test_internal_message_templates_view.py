from urllib.parse import urlencode

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import (
    with_internal_auth,
)
from insights.metrics.meta.clients import MetaGraphAPIClient


class BaseTestInternalMetaMessageTemplatesView(APITestCase):
    def get_templates_metrics_analytics(
        self, data: dict, query_params: dict
    ) -> Response:
        base_url = (
            "/v1/metrics/meta/internal/whatsapp-message-templates/messages-analytics/"
        )

        url_to_call = base_url
        if query_params:
            url_to_call = f"{base_url}?{urlencode(query_params)}"

        return self.client.post(url_to_call, data, format="json")


class TestInternalMetaMessageTemplatesViewAsAnonymousUser(
    BaseTestInternalMetaMessageTemplatesView
):
    def test_cannot_get_templates_metrics_analytics_not_authenticated(self):
        response = self.get_templates_metrics_analytics({}, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestInternalMetaMessageTemplatesViewAsAuthenticatedUser(
    BaseTestInternalMetaMessageTemplatesView
):
    def setUp(self):
        self.meta_api_client: MetaGraphAPIClient = MetaGraphAPIClient()
        self.user = User.objects.create()

        self.client.force_authenticate(self.user)
        cache.clear()

    @with_internal_auth
    def test_cannot_get_templates_metrics_analytics_without_required_fields(self):
        response = self.get_templates_metrics_analytics({}, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.data["errors"]["query_params"]["waba_id"][0].code, "required"
        )
        self.assertEqual(
            response.data["errors"]["query_params"]["start_date"][0].code, "required"
        )
        self.assertEqual(
            response.data["errors"]["query_params"]["end_date"][0].code, "required"
        )
        self.assertEqual(
            response.data["errors"]["body"]["template_ids"][0].code, "required"
        )
