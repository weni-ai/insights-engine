from unittest.mock import patch

from django.core.cache import cache
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.models import (
    FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD,
    FavoriteTemplate,
)
from insights.metrics.meta.choices import (
    WhatsAppMessageTemplatesCategories,
    WhatsAppMessageTemplatesLanguages,
)
from insights.projects.models import Project
from insights.metrics.meta.utils import (
    format_button_metrics_data,
    format_messages_metrics_data,
)
from insights.metrics.meta.tests.mock import (
    MOCK_SUCCESS_RESPONSE_BODY,
    MOCK_TEMPLATE_DAILY_ANALYTICS,
    MOCK_TEMPLATES_LIST_BODY,
)


class BaseTestMetaMessageTemplatesView(APITestCase):
    def get_list_templates(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/list-templates/"

        return self.client.get(url, query_params)

    def get_preview(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/preview/"

        return self.client.get(url, query_params)

    def get_messages_analytics(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/messages-analytics/"

        return self.client.get(url, query_params)

    def get_buttons_analytics(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/buttons-analytics/"

        return self.client.get(url, query_params)

    def add_template_to_favorites(self, data: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/"

        return self.client.post(url, data)

    def remove_template_from_favorites(self, data: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/remove-template-from-favorites/"

        return self.client.post(url, data)

    def get_favorite_templates(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/favorites/"

        return self.client.get(url, query_params)

    def get_categories(self) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/categories/"

        return self.client.get(url)

    def get_languages(self) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/languages/"

        return self.client.get(url)

    def get_wabas(self, query_params: dict) -> Response:
        url = "/v1/metrics/meta/whatsapp-message-templates/wabas/"

        return self.client.get(url, query_params)


class TestMetaMessageTemplatesViewAsAnonymousUser(BaseTestMetaMessageTemplatesView):
    def test_cannot_get_list_templates_when_not_authenticated(self):
        response = self.get_list_templates({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_preview_when_not_authenticated(self):
        response = self.get_preview({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_messages_analytics_when_not_authenticated(self):
        response = self.get_messages_analytics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_buttons_analytics_when_not_authenticated(self):
        response = self.get_buttons_analytics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_add_template_to_favorites_when_not_authenticated(self):
        response = self.add_template_to_favorites({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_remove_template_from_favorites_when_not_authenticated(self):
        response = self.remove_template_from_favorites({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_favorite_templates_when_not_authenticated(self):
        response = self.get_favorite_templates({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_categories_when_not_authenticated(self):
        response = self.get_categories()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_languages_when_not_authenticated(self):
        response = self.get_languages()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_wabas_when_not_authenticated(self):
        response = self.get_wabas({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMetaMessageTemplatesViewAsAuthenticatedUser(BaseTestMetaMessageTemplatesView):
    def setUp(self):
        self.meta_api_client: MetaGraphAPIClient = MetaGraphAPIClient()
        self.user = User.objects.create(language="pt_BR")
        self.project = Project.objects.create(name="test_project")

        self.client.force_authenticate(self.user)
        cache.clear()

    def test_cannot_get_list_templates_without_project_uuid_and_waba_id(self):
        response = self.get_list_templates({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_list_templates_when_user_does_not_have_project_permission(self):
        response = self.get_list_templates(
            {
                "project_uuid": self.project.uuid,
                "waba_id": "0000000000000000",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_list_templates_when_waba_id_is_not_related_to_project(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        mock_wabas.return_value = []
        response = self.get_list_templates(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_get_list_templates_with_invalid_limit(
        self, mock_list_templates, mock_wabas
    ):
        mock_list_templates.return_value = MOCK_TEMPLATES_LIST_BODY
        mock_wabas.return_value = [{"waba_id": "0000000000000000"}]
        response = self.get_list_templates(
            {
                "waba_id": "0000000000000000",
                "project_uuid": self.project.uuid,
                "limit": 51,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["limit"][0].code, "limit_too_large")

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_cannot_get_list_templates_with_invalid_category(
        self, mock_list_templates, mock_wabas
    ):
        mock_list_templates.return_value = MOCK_TEMPLATES_LIST_BODY
        mock_wabas.return_value = [{"waba_id": "0000000000000000"}]

        response = self.get_list_templates(
            {
                "waba_id": "0000000000000000",
                "project_uuid": self.project.uuid,
                "category": "INVALID_CATEGORY",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["category"][0].code, "invalid_choice")

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_cannot_get_list_templates_with_invalid_language(
        self, mock_list_templates, mock_wabas
    ):
        mock_list_templates.return_value = MOCK_TEMPLATES_LIST_BODY
        mock_wabas.return_value = [{"waba_id": "0000000000000000"}]

        response = self.get_list_templates(
            {
                "waba_id": "0000000000000000",
                "project_uuid": self.project.uuid,
                "language": "INVALID_LANGUAGE",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["language"][0].code, "invalid_choice")

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_get_list_templates(self, mock_list_templates, mock_wabas):
        waba_id = "0000000000000000"
        mock_wabas.return_value = [{"waba_id": waba_id}]
        mock_list_templates.return_value = MOCK_TEMPLATES_LIST_BODY
        response = self.get_list_templates(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MOCK_TEMPLATES_LIST_BODY)

    def test_cannot_get_preview_without_project_uuid_and_waba_id(self):
        response = self.get_preview({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview")
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

        expected_response = MOCK_SUCCESS_RESPONSE_BODY.copy()
        expected_response["is_favorite"] = False

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_response)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview")
    def test_get_preview_for_favorite_template(self, mock_preview, mock_wabas):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project, config={"waba_id": waba_id}
        )
        FavoriteTemplate.objects.create(
            dashboard=dashboard, template_id=template_id, name="test_template"
        )
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

        expected_response = MOCK_SUCCESS_RESPONSE_BODY.copy()
        expected_response["is_favorite"] = True

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_response)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_get_messages_analytics(self, mock_analytics, mock_wabas):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]
        expected_response = {
            "data": format_messages_metrics_data(
                MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
            )
        }
        mock_analytics.return_value = expected_response

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
        self.assertEqual(response.data, expected_response)

    def test_cannot_get_messages_analytics_without_project_uuid_and_waba_id(self):
        response = self.get_messages_analytics({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
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

    def test_cannot_get_buttons_analytics_without_project_uuid_and_waba_id(self):
        response = self.get_buttons_analytics({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_buttons_analytics_when_waba_id_is_not_related_to_project(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = []
        response = self.get_buttons_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_buttons_analytics_when_user_does_not_have_project_permission(
        self, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_buttons_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_buttons_analytics")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview")
    def test_get_buttons_analytics(
        self, mock_preview, mock_buttons_analytics, mock_wabas
    ):
        waba_id = "0000000000000000"
        template_id = "1234567890987654"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]
        mock_preview.return_value = MOCK_SUCCESS_RESPONSE_BODY

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

        mock_buttons_analytics.return_value = expected_response

        response = self.get_buttons_analytics(
            {
                "waba_id": waba_id,
                "project_uuid": self.project.uuid,
                "template_id": template_id,
                "start_date": str(timezone.now().date() - timedelta(days=7)),
                "end_date": str(timezone.now().date()),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_response)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_buttons_analytics_missing_required_params(self, mock_wabas):
        waba_id = "0000000000000000"
        mock_wabas.return_value = [
            {"waba_id": waba_id},
        ]

        response = self.get_buttons_analytics(
            {"waba_id": waba_id, "project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"].code, "required_fields_missing")
        self.assertEqual(
            response.data,
            {"error": "Required fields are missing: template_id, start_date, end_date"},
        )

    @with_project_auth
    def test_cannot_add_template_to_favorites_without_required_fields(self):
        response = self.add_template_to_favorites({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["dashboard"][0].code, "required")
        self.assertEqual(response.data["template_id"][0].code, "required")

    @with_project_auth
    def test_cannot_add_template_to_favorites_when_dashboard_is_not_related_to_project(
        self,
    ):
        project = Project.objects.create(name="test_project")
        dashboard = Dashboard.objects.create(name="test_dashboard", project=project)

        response = self.add_template_to_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": "1234567890987654",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["dashboard"][0].code, "does_not_exist")

    @with_project_auth
    def test_cannot_add_template_to_favorites_when_template_is_already_in_favorites(
        self,
    ):
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project
        )

        FavoriteTemplate.objects.create(
            dashboard=dashboard,
            template_id="1234567890987654",
            name="test_template",
        )

        response = self.add_template_to_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": "1234567890987654",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["template_id"][0].code, "template_already_in_favorites"
        )

    @with_project_auth
    def test_cannot_add_template_to_favorites_when_the_limit_is_reached(self):
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project
        )

        FavoriteTemplate.objects.bulk_create(
            [
                FavoriteTemplate(
                    dashboard=dashboard,
                    template_id=str(i),
                    name="test_template",
                )
                for i in range(FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD)
            ]
        )

        response = self.add_template_to_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": str(FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["dashboard"][0].code, "favorite_template_limit_reached"
        )

    @with_project_auth
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview")
    def test_add_template_to_favorites(self, mock_preview):
        mock_preview.return_value = MOCK_SUCCESS_RESPONSE_BODY

        dashboard = Dashboard.objects.create(
            name="test_dashboard",
            project=self.project,
            config={"waba_id": "0000000000000000"},
        )

        template_id = MOCK_SUCCESS_RESPONSE_BODY.get("id")
        template_name = MOCK_SUCCESS_RESPONSE_BODY.get("name")

        response = self.add_template_to_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        favorite = FavoriteTemplate.objects.get(
            dashboard=dashboard, template_id=template_id
        )

        self.assertEqual(favorite.name, template_name)

    @with_project_auth
    def test_cannot_remove_template_from_favorites_without_required_fields(self):
        response = self.remove_template_from_favorites({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["dashboard"][0].code, "required")
        self.assertEqual(response.data["template_id"][0].code, "required")

    @with_project_auth
    def test_cannot_remove_template_from_favorites_when_dashboard_is_not_related_to_project(
        self,
    ):
        project = Project.objects.create(name="test_project")
        dashboard = Dashboard.objects.create(name="test_dashboard", project=project)

        response = self.remove_template_from_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": "1234567890987654",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["dashboard"][0].code, "does_not_exist")

    @with_project_auth
    def test_cannot_remove_template_from_favorites_when_template_is_not_in_favorites(
        self,
    ):
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project
        )

        response = self.remove_template_from_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": "1234567890987654",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["template_id"][0].code, "template_not_in_favorites"
        )

    @with_project_auth
    def test_remove_template_from_favorites(self):
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project
        )

        template_id = "1234567890987654"

        FavoriteTemplate.objects.create(
            dashboard=dashboard, template_id=template_id, name="test_template"
        )

        response = self.remove_template_from_favorites(
            {
                "dashboard": dashboard.uuid,
                "template_id": template_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            FavoriteTemplate.objects.filter(
                dashboard=dashboard, template_id=template_id
            ).exists()
        )

    def test_cannot_get_favorite_templates_without_project_authorization(self):
        dashboard = Dashboard.objects.create(
            name="test_dashboard", project=self.project
        )

        FavoriteTemplate.objects.create(
            dashboard=dashboard, template_id="1234567890987654", name="test_template"
        )

        response = self.get_favorite_templates({"dashboard": dashboard.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["dashboard"][0].code, "does_not_exist")

    @with_project_auth
    def test_get_favorite_templates(self):
        waba_id = "1234567890987654"

        dashboard = Dashboard.objects.create(
            name="test_dashboard",
            project=self.project,
            config={"waba_id": waba_id},
        )

        favorite = FavoriteTemplate.objects.create(
            dashboard=dashboard, template_id="1234567890987654", name="test_template"
        )

        response = self.get_favorite_templates({"dashboard": dashboard.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(
            response.data["count"],
            FavoriteTemplate.objects.filter(dashboard=dashboard).count(),
        )
        self.assertEqual(
            response.data["results"][0],
            {
                "template_id": favorite.template_id,
                "name": favorite.name,
                "waba_id": waba_id,
                "project_uuid": str(dashboard.project.uuid),
            },
        )

    def test_get_categories(self):
        response = self.get_categories()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "categories": [
                    {
                        "value": category.value,
                        "name": category.label,
                    }
                    for category in WhatsAppMessageTemplatesCategories
                ]
            },
        )

    def test_get_languages(self):
        response = self.get_languages()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "languages": [
                    {"value": language.value, "name": language.label}
                    for language in WhatsAppMessageTemplatesLanguages
                ]
            },
        )

    def test_cannot_get_wabas_without_project_authorization(self):
        response = self.get_wabas({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_get_wabas(self, mock_wabas):
        mock_wabas.return_value = [
            {
                "waba_id": "1234567890987654",
                "phone_number": {
                    "id": "000000000000000",
                    "display_name": "Test",
                    "display_phone_number": "+55 84 9988-7766",
                },
            },
            {
                "waba_id": "9876543210123456",
                "phone_number": {
                    "id": "111111111111111",
                    "display_name": "Test 2",
                    "display_phone_number": "+55 84 8877-6655",
                },
            },
        ]

        response = self.get_wabas({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "results": [
                    {
                        "id": "1234567890987654",
                        "phone_number": "+55 84 9988-7766",
                    },
                    {
                        "id": "9876543210123456",
                        "phone_number": "+55 84 8877-6655",
                    },
                ],
            },
        )
