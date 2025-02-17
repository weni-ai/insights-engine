import json
import responses
from unittest.mock import patch

from django.core.cache import cache
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project
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
        self.user = User.objects.create()
        self.project = Project.objects.create(name="test_project")

        self.client.force_authenticate(self.user)
        cache.clear()

    def test_cannot_get_preview_without_project_uuid_and_waba_id(self):
        response = self.get_preview({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_preview_when_waba_id_is_not_related_to_project(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = []
        response = self.get_preview(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_preview_when_user_does_not_have_project_permission(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_preview(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch(
        "insights.sources.meta_message_templates.clients.MetaAPIClient.get_template_preview"
    )
    def test_get_preview(self, mock_preview, mock_wabas):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]
        mock_preview.return_value = MOCK_SUCCESS_RESPONSE_BODY

        response = self.get_preview(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MOCK_SUCCESS_RESPONSE_BODY)

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_preview_missing_template_id(self, mock_wabas):
        waba_id = "0000000000000000"

        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_preview(
            {"waba_id": waba_id, "project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "template_id_missing")

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch(
        "insights.sources.meta_message_templates.clients.MetaAPIClient.get_messages_analytics"
    )
    def test_get_messages_analytics(self, mock_analytics, mock_wabas):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]
        mock_analytics.return_value = {
            "data": format_messages_metrics_data(
                MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
            )
        }

        response = self.get_messages_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
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

    def test_cannot_get_messages_analytics_without_project_uuid_and_waba_id(self):
        response = self.get_messages_analytics({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_messages_analytics_when_waba_id_is_not_related_to_project(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = []
        response = self.get_messages_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_messages_analytics_when_user_does_not_have_project_permission(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_messages_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_messages_analytics_missing_required_params(self, mock_wabas):
        response = self.get_messages_analytics({})
        waba_id = "0000000000000000"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_messages_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "required_fields_missing")
        self.assertEqual(
            response.data,
            {"error": "Required fields are missing: template_id, start_date, end_date"},
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
