from unittest.mock import patch

import responses

from django.conf import settings
from django.test import TestCase, override_settings

from insights.sources.integrations.clients import NexusClient


@override_settings(NEXUS_BASE_URL="https://nexus.weni.ai")
class TestNexusClient(TestCase):
    def setUp(self):
        self.client = NexusClient()

    def test_base_url(self):
        self.assertEqual(self.client.base_url, settings.NEXUS_BASE_URL)

    def test_get_headers_api_token(self):
        self.assertEqual(
            self.client.get_headers(NexusClient.AuthTypes.API_TOKEN),
            {
                "Authorization": f"Bearer {settings.NEXUS_API_TOKEN}",
            },
        )

    @patch(
        "insights.sources.integrations.clients.InternalAuthentication.get_module_token",
        return_value="Bearer internal-token",
    )
    def test_get_headers_keycloak_internal(self, mock_get_module_token):
        self.assertEqual(
            self.client.get_headers(NexusClient.AuthTypes.KEYCLOAK_INTERNAL),
            {
                "Content-Type": "application/json; charset: utf-8",
                "Authorization": "Bearer internal-token",
            },
        )
        mock_get_module_token.assert_called_once()

    def test_get_headers_invalid_auth_type(self):
        with self.assertRaises(ValueError):
            self.client.get_headers("invalid-auth-type")

    def test_get_project_multi_agents_status(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_BASE_URL}/project/123/multi-agents",
                json={"multi_agents": True},
                status=200,
            )
            response = self.client.get_project_multi_agents_status(project_uuid="123")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"multi_agents": True})

            self.assertEqual(len(rsps.calls), 1)

    @patch(
        "insights.sources.integrations.clients.InternalAuthentication.get_module_token",
        return_value="Bearer internal-token",
    )
    def test_get_project_agents_team(self, mock_get_module_token):
        agents_team = {
            "manager": {"external_id": ""},
            "agents": [
                {
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "slug": "agent-slug",
                    "name": "Agent Name",
                    "about": {"en": "", "pt": None, "es": None},
                    "group": None,
                    "is_official": True,
                    "mcps": None,
                    "active": True,
                }
            ],
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_BASE_URL}/agents/teams/123",
                json=agents_team,
                status=200,
            )
            response = self.client.get_project_agents_team(project_uuid="123")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), agents_team)

            self.assertEqual(len(rsps.calls), 1)

        mock_get_module_token.assert_called_once()
