from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.commerce.exceptions import BillingRequestError
from insights.projects.models import Project


ABANDONED_CART_URL = "/v1/commerce/abandoned-cart/status/"
MARKETING_PRICING_URL = "/v1/commerce/marketing-pricing/"


class TestAbandonedCartStatusViewAsAnonymousUser(APITestCase):
    def test_cannot_access_when_not_authenticated(self):
        response = self.client.get(ABANDONED_CART_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAbandonedCartStatusView(APITestCase):
    def setUp(self):
        self.user = User.objects.create(language="pt_BR")
        self.project = Project.objects.create(name="test_project")
        self.client.force_authenticate(self.user)

    def test_returns_400_when_project_uuid_is_missing(self):
        response = self.client.get(ABANDONED_CART_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_when_user_does_not_have_project_permission(self):
        response = self.client.get(
            ABANDONED_CART_URL, {"project_uuid": str(self.project.uuid)}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch("insights.commerce.views.AbandonedCartStatusService.is_active")
    def test_returns_active_true(self, mock_is_active):
        mock_is_active.return_value = True

        response = self.client.get(
            ABANDONED_CART_URL, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"active": True})

    @with_project_auth
    @patch("insights.commerce.views.AbandonedCartStatusService.is_active")
    def test_returns_active_false(self, mock_is_active):
        mock_is_active.return_value = False

        response = self.client.get(
            ABANDONED_CART_URL, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"active": False})


class TestMarketingPricingViewAsAnonymousUser(APITestCase):
    def test_cannot_access_when_not_authenticated(self):
        response = self.client.get(MARKETING_PRICING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMarketingPricingView(APITestCase):
    def setUp(self):
        self.user = User.objects.create(language="pt_BR")
        self.project = Project.objects.create(name="test_project")
        self.client.force_authenticate(self.user)

    def test_returns_400_when_project_uuid_is_missing(self):
        response = self.client.get(MARKETING_PRICING_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_when_user_does_not_have_project_permission(self):
        response = self.client.get(
            MARKETING_PRICING_URL, {"project_uuid": str(self.project.uuid)}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch("insights.commerce.views.MarketingPricingService.get_marketing_pricing")
    def test_returns_marketing_value(self, mock_get_pricing):
        mock_get_pricing.return_value = {"value": 0.5, "currency": "BRL"}

        response = self.client.get(
            MARKETING_PRICING_URL, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"value": 0.5, "currency": "BRL"})

    @with_project_auth
    @patch("insights.commerce.views.MarketingPricingService.get_marketing_pricing")
    def test_returns_502_when_billing_fails(self, mock_get_pricing):
        mock_get_pricing.side_effect = BillingRequestError("boom")

        response = self.client.get(
            MARKETING_PRICING_URL, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
