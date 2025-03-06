import uuid
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class BaseTestWhatsappIntegrationWebhook(APITestCase):
    def receive_integration_data(self, data: dict) -> Response:
        url = "/v1/metrics/meta/internal/whatsapp-integration/"

        return self.client.post(url, data)

    def remove_integration(self, data: dict) -> Response:
        url = "/v1/metrics/meta/internal/whatsapp-integration/"

        return self.client.delete(url, data)


class TestWhatsappIntegrationWebhookAsAnonymousUser(BaseTestWhatsappIntegrationWebhook):
    def test_cannot_receive_integration_data_when_unauthenticated(self):
        response = self.receive_integration_data({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_remove_integration_when_unauthenticated(self):
        response = self.remove_integration({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestWhatsappIntegrationWebhookAsAuthenticatedUser(
    BaseTestWhatsappIntegrationWebhook
):
    def test_receive_new_integration_data(self):
        project = Project.objects.create()

        self.assertFalse(
            Dashboard.objects.filter(
                project=project, config__is_whatsapp_integration=True
            ).exists()
        )

        payload = {
            "project_uuid": project.uuid,
            "waba_id": "1234567890",
            "phone_number": {
                "id": "445303688657575",
                "display_phone_number": "+55 82 98877 6655",
            },
        }

        response = self.receive_integration_data(payload)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        dashboard = Dashboard.objects.filter(
            project=project, config__is_whatsapp_integration=True
        ).first()
        self.assertIsNotNone(dashboard)

        self.assertIn("waba_id", dashboard.config)
        self.assertEqual(dashboard.config["waba_id"], payload["waba_id"])

        self.assertIn("phone_number", dashboard.config)
        self.assertEqual(dashboard.config["phone_number"], payload["phone_number"])

        self.assertIn("default_template", dashboard.config)
        self.assertIsNone(dashboard.config["default_template"])

    def test_receive_integration_data_when_integration_already_exists(self):
        project = Project.objects.create()
        waba_id = "1234567890"

        dashboard = Dashboard.objects.create(
            project=project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": waba_id,
                "phone_number": {
                    "id": "556622598897977",
                    "display_phone_number": "+55 82 98877 6655",
                },
            },
        )

        payload = {
            "project_uuid": project.uuid,
            "waba_id": waba_id,
            "phone_number": {
                "id": "996622598897977",
                "display_phone_number": "+55 84 91122 5566",
            },
        }

        response = self.receive_integration_data(payload)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        dashboard.refresh_from_db(fields=["config"])

        self.assertEqual(
            dashboard.config["phone_number"]["display_phone_number"],
            payload["phone_number"]["display_phone_number"],
        )
        self.assertEqual(
            dashboard.config["phone_number"]["id"], payload["phone_number"]["id"]
        )

    def test_cannot_receive_integration_when_missing_required_fields(self):
        response = self.receive_integration_data({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["waba_id"][0].code, "required")
        self.assertEqual(response.data["phone_number"][0].code, "required")

    def test_cannot_receive_integration_when_missing_phone_number_required_fields(self):
        response = self.receive_integration_data(
            {
                "project_uuid": uuid.uuid4(),
                "waba_id": "1234567890",
                "phone_number": {},
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["phone_number"]["id"][0].code, "required")
        self.assertEqual(
            response.data["phone_number"]["display_phone_number"][0].code, "required"
        )

    def test_cannot_receive_integration_for_non_existent_project(self):
        response = self.receive_integration_data(
            {
                "project_uuid": uuid.uuid4(),
                "waba_id": "1234567890",
                "phone_number": {
                    "id": "123456789123456",
                    "display_phone_number": "+55 82 98877 6655",
                },
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_integration(self):
        project = Project.objects.create()
        waba_id = "1234567890"

        Dashboard.objects.create(
            project=project,
            config__is_whatsapp_integration=True,
            config__waba_id=waba_id,
        )

        self.assertTrue(
            Dashboard.objects.filter(
                project=project,
                config__is_whatsapp_integration=True,
                config__waba_id=waba_id,
            ).exists()
        )

        response = self.remove_integration(
            {
                "project_uuid": project.uuid,
                "waba_id": waba_id,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            Dashboard.objects.filter(
                project=project,
                config__is_whatsapp_integration=True,
                config__waba_id=waba_id,
            ).exists()
        )

    def test_cannot_remove_integration_when_missing_required_fields(self):
        response = self.remove_integration({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["waba_id"][0].code, "required")

    def test_cannot_remove_integration_for_non_existent_project(self):
        response = self.remove_integration(
            {
                "project_uuid": uuid.uuid4(),
                "waba_id": "1234567890",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_remove_integration_when_integration_does_not_exist(self):
        response = self.remove_integration(
            {
                "project_uuid": uuid.uuid4(),
                "waba_id": "1234567890",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
