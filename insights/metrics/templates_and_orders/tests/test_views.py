from unittest.mock import patch

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_internal_auth
from insights.projects.models import Project


URL = "/v1/metrics/internal/templates-and-orders/"


class BaseTestTemplatesAndOrdersView(APITestCase):
    def get_metrics(self, params: dict) -> Response:
        return self.client.get(URL, params)


class TestAsAnonymousUser(BaseTestTemplatesAndOrdersView):
    def test_returns_401_when_unauthenticated(self):
        response = self.get_metrics({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAsAuthenticatedUserWithoutInternalPermission(
    BaseTestTemplatesAndOrdersView
):
    def setUp(self):
        self.user = User.objects.create_user(email="test@mail.com")
        self.project = Project.objects.create()
        self.client.force_authenticate(self.user)

    def test_returns_403_without_internal_permission(self):
        response = self.get_metrics({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestAsInternalUser(BaseTestTemplatesAndOrdersView):
    def setUp(self):
        self.user = User.objects.create_user(email="internal@mail.com")
        self.project = Project.objects.create()
        self.client.force_authenticate(self.user)

        self.valid_params = {
            "project_uuid": str(self.project.uuid),
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "utm_source": "weniabandonedcart",
            "template_name_prefix": "weni_abandoned_cart",
        }

    @with_internal_auth
    def test_returns_400_when_project_uuid_is_missing(self):
        params = self.valid_params.copy()
        del params["project_uuid"]
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_internal_auth
    def test_returns_400_when_start_date_is_missing(self):
        params = self.valid_params.copy()
        del params["start_date"]
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_internal_auth
    def test_returns_400_when_end_date_is_missing(self):
        params = self.valid_params.copy()
        del params["end_date"]
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_internal_auth
    def test_returns_400_when_utm_source_is_missing(self):
        params = self.valid_params.copy()
        del params["utm_source"]
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_internal_auth
    def test_returns_400_when_template_name_prefix_is_missing(self):
        params = self.valid_params.copy()
        del params["template_name_prefix"]
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_internal_auth
    def test_returns_404_when_project_does_not_exist(self):
        params = self.valid_params.copy()
        params["project_uuid"] = "00000000-0000-0000-0000-000000000000"
        response = self.get_metrics(params)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_returns_200_with_correct_response_format(self, MockUseCase):
        mock_instance = MockUseCase.return_value
        mock_instance.execute.return_value = {
            "template_metrics": {
                "sent": 5,
                "delivered": 5,
                "read": 4,
                "clicked": 2,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 25200.82,
                    "currency_code": "BRL",
                    "increase_percentage": 100,
                },
                "orders_placed": {
                    "value": 65,
                    "increase_percentage": 100,
                },
            },
        }

        response = self.get_metrics(self.valid_params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data["templates_metrics"],
            {"sent": 5, "delivered": 5, "read": 4, "clicked": 2},
        )
        self.assertEqual(response.data["orders"]["revenue"]["value"], 25200.82)
        self.assertEqual(response.data["orders"]["revenue"]["currency_code"], "R$")
        self.assertEqual(
            response.data["orders"]["revenue"]["increase_percentage"], 100
        )
        self.assertEqual(response.data["orders"]["orders_placed"]["value"], 65)
        self.assertEqual(
            response.data["orders"]["orders_placed"]["increase_percentage"], 100
        )

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_returns_correct_currency_symbol_for_usd(self, MockUseCase):
        mock_instance = MockUseCase.return_value
        mock_instance.execute.return_value = {
            "template_metrics": {
                "sent": 10,
                "delivered": 8,
                "read": 5,
                "clicked": 3,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 1000.00,
                    "currency_code": "USD",
                    "increase_percentage": 50.0,
                },
                "orders_placed": {
                    "value": 10,
                    "increase_percentage": 25.0,
                },
            },
        }

        response = self.get_metrics(self.valid_params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["orders"]["revenue"]["currency_code"], "US$"
        )

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_returns_empty_currency_code_when_not_provided(self, MockUseCase):
        mock_instance = MockUseCase.return_value
        mock_instance.execute.return_value = {
            "template_metrics": {
                "sent": 0,
                "delivered": 0,
                "read": 0,
                "clicked": 0,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 0,
                    "currency_code": "",
                    "increase_percentage": 0,
                },
                "orders_placed": {
                    "value": 0,
                    "increase_percentage": 0,
                },
            },
        }

        response = self.get_metrics(self.valid_params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["orders"]["revenue"]["currency_code"], "")

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_returns_502_when_orders_service_fails(self, MockUseCase):
        from insights.metrics.templates_and_orders.exceptions import (
            ErrorGettingOrdersMetrics,
        )

        mock_instance = MockUseCase.return_value
        mock_instance.execute.side_effect = ErrorGettingOrdersMetrics(
            "Error getting orders from VTEX"
        )

        response = self.get_metrics(self.valid_params)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_returns_500_on_unexpected_error(self, MockUseCase):
        mock_instance = MockUseCase.return_value
        mock_instance.execute.side_effect = Exception("Unexpected failure")

        response = self.get_metrics(self.valid_params)

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertIn("error", response.data)

    @with_internal_auth
    @patch(
        "insights.metrics.templates_and_orders.views.GetTemplatesAndOrdersMetrics"
    )
    def test_passes_correct_params_to_use_case(self, MockUseCase):
        mock_instance = MockUseCase.return_value
        mock_instance.execute.return_value = {
            "template_metrics": {
                "sent": 0,
                "delivered": 0,
                "read": 0,
                "clicked": 0,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 0,
                    "currency_code": "",
                    "increase_percentage": 0,
                },
                "orders_placed": {
                    "value": 0,
                    "increase_percentage": 0,
                },
            },
        }

        self.get_metrics(self.valid_params)

        from datetime import date

        mock_instance.execute.assert_called_once_with(
            project=self.project,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            utm_source="weniabandonedcart",
            template_name_prefix="weni_abandoned_cart",
        )
