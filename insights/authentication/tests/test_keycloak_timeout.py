from unittest.mock import patch

import requests
from django.test import TestCase, override_settings

from insights.authentication.authentication import FlowsInternalAuthentication
from insights.internals.base import InternalAuthentication

KEYCLOAK_SETTINGS = {
    "OIDC_OP_TOKEN_ENDPOINT": "https://keycloak.example/realms/weni/protocol/openid-connect/token",
    "OIDC_RP_CLIENT_ID": "insights-client",
    "OIDC_RP_CLIENT_SECRET": "client-secret",
    "OIDC_TIMEOUT": 15,
}


@override_settings(**KEYCLOAK_SETTINGS)
class TestInternalAuthenticationKeycloakTimeout(TestCase):
    @patch("insights.internals.base.requests.post")
    def test_get_module_token_passes_configured_timeout(self, mock_post):
        mock_post.return_value.json.return_value = {"access_token": "internal-token"}

        token = InternalAuthentication().get_module_token()

        mock_post.assert_called_once_with(
            url=KEYCLOAK_SETTINGS["OIDC_OP_TOKEN_ENDPOINT"],
            data={
                "client_id": KEYCLOAK_SETTINGS["OIDC_RP_CLIENT_ID"],
                "client_secret": KEYCLOAK_SETTINGS["OIDC_RP_CLIENT_SECRET"],
                "grant_type": "client_credentials",
            },
            timeout=KEYCLOAK_SETTINGS["OIDC_TIMEOUT"],
        )
        self.assertEqual(token, "Bearer internal-token")

    @patch("insights.internals.base.requests.post")
    def test_get_module_token_propagates_timeout_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(requests.exceptions.Timeout):
            InternalAuthentication().get_module_token()


@override_settings(**KEYCLOAK_SETTINGS, FLOWS_URL="https://flows.example")
class TestFlowsInternalAuthenticationKeycloakTimeout(TestCase):
    @patch("insights.authentication.authentication.requests.post")
    def test_get_module_token_passes_configured_timeout(self, mock_post):
        mock_post.return_value.json.return_value = {"access_token": "flows-token"}

        token = FlowsInternalAuthentication().get_module_token()

        mock_post.assert_called_once_with(
            url=KEYCLOAK_SETTINGS["OIDC_OP_TOKEN_ENDPOINT"],
            data={
                "client_id": KEYCLOAK_SETTINGS["OIDC_RP_CLIENT_ID"],
                "client_secret": KEYCLOAK_SETTINGS["OIDC_RP_CLIENT_SECRET"],
                "grant_type": "client_credentials",
            },
            timeout=KEYCLOAK_SETTINGS["OIDC_TIMEOUT"],
        )
        self.assertEqual(token, "Bearer flows-token")

    @patch("insights.authentication.authentication.requests.post")
    def test_get_module_token_propagates_timeout_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(requests.exceptions.Timeout):
            FlowsInternalAuthentication().get_module_token()
