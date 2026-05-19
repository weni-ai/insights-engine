import json
from unittest.mock import patch

import responses
from django.test import TestCase, override_settings
from rest_framework import status

from insights.commerce.clients import BillingClient, RetailSetupClient
from insights.commerce.tests.mock import (
    MOCK_AGENTS_WITH_LEGACY_CART,
    MOCK_INTEGRATED_FEATURES_WITH_CART,
    MOCK_META_PRICING_RESPONSE,
)


@override_settings(RETAIL_URL="https://retailsetup.test.weni.ai")
class TestRetailSetupClient(TestCase):
    def setUp(self):
        self.project_uuid = "11111111-1111-1111-1111-111111111111"

    @patch(
        "insights.internals.base.InternalAuthentication.get_module_token",
        return_value="Bearer fake-token",
    )
    def test_get_project_integrated_features(self, _mock_token):
        client = RetailSetupClient()
        url = f"{client.base_url}/v2/app_integrated_feature/{self.project_uuid}/"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_INTEGRATED_FEATURES_WITH_CART),
            )

            response = client.get_project_integrated_features(self.project_uuid)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), MOCK_INTEGRATED_FEATURES_WITH_CART)
            self.assertEqual(len(rsps.calls), 1)

    @patch(
        "insights.internals.base.InternalAuthentication.get_module_token",
        return_value="Bearer fake-token",
    )
    def test_get_project_agents(self, _mock_token):
        client = RetailSetupClient()
        url = f"{client.base_url}/v2/agents/{self.project_uuid}/"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_AGENTS_WITH_LEGACY_CART),
            )

            response = client.get_project_agents(self.project_uuid)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), MOCK_AGENTS_WITH_LEGACY_CART)


@override_settings(BILLING_URL="https://billing.test.weni.ai")
class TestBillingClient(TestCase):
    def setUp(self):
        self.project_uuid = "22222222-2222-2222-2222-222222222222"

    @patch(
        "insights.internals.base.InternalAuthentication.get_module_token",
        return_value="Bearer fake-token",
    )
    def test_get_meta_pricing(self, _mock_token):
        client = BillingClient()
        url = f"{client.base_url}/api/v1/meta-pricing/"

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url,
                status=status.HTTP_200_OK,
                content_type="application/json",
                body=json.dumps(MOCK_META_PRICING_RESPONSE),
            )

            response = client.get_meta_pricing(self.project_uuid)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), MOCK_META_PRICING_RESPONSE)
            self.assertEqual(len(rsps.calls), 1)
            self.assertIn(
                f"project_uuid={self.project_uuid}", rsps.calls[0].request.url
            )
