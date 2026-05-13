from unittest.mock import MagicMock

from django.test import TestCase, override_settings
from rest_framework import status

from insights.commerce.exceptions import (
    BillingRequestError,
    RetailSetupRequestError,
)
from insights.commerce.services import (
    AbandonedCartStatusService,
    MarketingPricingService,
)
from insights.commerce.tests.mock import (
    MOCK_AGENTS_WITH_LEGACY_CART,
    MOCK_AGENTS_WITH_LEGACY_CART_NOT_ASSIGNED,
    MOCK_AGENTS_WITHOUT_LEGACY_CART,
    MOCK_INTEGRATED_FEATURES_EMPTY,
    MOCK_INTEGRATED_FEATURES_WITH_CART,
    MOCK_INTEGRATED_FEATURES_WITHOUT_CART,
    MOCK_META_PRICING_RESPONSE,
)


def _build_response(status_code: int, payload):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


class TestAbandonedCartStatusService(TestCase):
    def setUp(self):
        self.project_uuid = "11111111-1111-1111-1111-111111111111"
        self.client = MagicMock()
        self.service = AbandonedCartStatusService(client=self.client)
        self.service.cache = MagicMock()
        self.service.cache.get.return_value = None

    def test_returns_true_when_new_model_has_abandoned_cart(self):
        self.client.get_project_integrated_features.return_value = _build_response(
            status.HTTP_200_OK, MOCK_INTEGRATED_FEATURES_WITH_CART
        )

        self.assertTrue(self.service.is_active(self.project_uuid))
        self.client.get_project_agents.assert_not_called()

    def test_returns_true_when_legacy_model_has_assigned_cart_agent(self):
        self.client.get_project_integrated_features.return_value = _build_response(
            status.HTTP_200_OK, MOCK_INTEGRATED_FEATURES_WITHOUT_CART
        )
        self.client.get_project_agents.return_value = _build_response(
            status.HTTP_200_OK, MOCK_AGENTS_WITH_LEGACY_CART
        )

        self.assertTrue(self.service.is_active(self.project_uuid))

    def test_returns_false_when_legacy_cart_agent_is_not_assigned(self):
        self.client.get_project_integrated_features.return_value = _build_response(
            status.HTTP_200_OK, MOCK_INTEGRATED_FEATURES_EMPTY
        )
        self.client.get_project_agents.return_value = _build_response(
            status.HTTP_200_OK, MOCK_AGENTS_WITH_LEGACY_CART_NOT_ASSIGNED
        )

        self.assertFalse(self.service.is_active(self.project_uuid))

    def test_returns_false_when_neither_model_has_cart(self):
        self.client.get_project_integrated_features.return_value = _build_response(
            status.HTTP_200_OK, MOCK_INTEGRATED_FEATURES_EMPTY
        )
        self.client.get_project_agents.return_value = _build_response(
            status.HTTP_200_OK, MOCK_AGENTS_WITHOUT_LEGACY_CART
        )

        self.assertFalse(self.service.is_active(self.project_uuid))

    def test_returns_false_when_new_model_request_fails(self):
        self.client.get_project_integrated_features.side_effect = (
            RetailSetupRequestError("boom")
        )
        self.client.get_project_agents.return_value = _build_response(
            status.HTTP_200_OK, MOCK_AGENTS_WITHOUT_LEGACY_CART
        )

        self.assertFalse(self.service.is_active(self.project_uuid))

    def test_returns_false_when_new_model_returns_non_success(self):
        self.client.get_project_integrated_features.return_value = _build_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )
        self.client.get_project_agents.return_value = _build_response(
            status.HTTP_200_OK, MOCK_AGENTS_WITHOUT_LEGACY_CART
        )

        self.assertFalse(self.service.is_active(self.project_uuid))

    def test_uses_cache_when_available(self):
        self.service.cache.get.return_value = "true"

        self.assertTrue(self.service.is_active(self.project_uuid))
        self.client.get_project_integrated_features.assert_not_called()
        self.client.get_project_agents.assert_not_called()


@override_settings(BILLING_URL="https://billing.test.weni.ai")
class TestMarketingPricingService(TestCase):
    def setUp(self):
        self.project_uuid = "22222222-2222-2222-2222-222222222222"
        self.client = MagicMock()
        self.service = MarketingPricingService(client=self.client)
        self.service.cache = MagicMock()
        self.service.cache.get.return_value = None

    def test_returns_marketing_value_from_billing(self):
        self.client.get_meta_pricing.return_value = _build_response(
            status.HTTP_200_OK, MOCK_META_PRICING_RESPONSE
        )

        data = self.service.get_marketing_pricing(self.project_uuid)

        self.assertEqual(data, {"value": 0.5, "currency": "BRL"})

    def test_raises_when_billing_returns_non_success(self):
        self.client.get_meta_pricing.return_value = _build_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )

        with self.assertRaises(BillingRequestError):
            self.service.get_marketing_pricing(self.project_uuid)

    def test_returns_zero_when_marketing_value_is_missing(self):
        self.client.get_meta_pricing.return_value = _build_response(
            status.HTTP_200_OK,
            {"currency": "BRL", "rates": {"utility": "0"}},
        )

        data = self.service.get_marketing_pricing(self.project_uuid)

        self.assertEqual(data, {"value": 0.0, "currency": "BRL"})

    @override_settings(BILLING_URL="")
    def test_raises_when_billing_url_not_configured(self):
        with self.assertRaises(BillingRequestError):
            self.service.get_marketing_pricing(self.project_uuid)

    def test_uses_cache_when_available(self):
        self.service.cache.get.return_value = '{"value": 0.75, "currency": "USD"}'

        data = self.service.get_marketing_pricing(self.project_uuid)

        self.assertEqual(data, {"value": 0.75, "currency": "USD"})
        self.client.get_meta_pricing.assert_not_called()
